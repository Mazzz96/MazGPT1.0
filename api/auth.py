# FastAPI backend for authentication and user management
from fastapi import APIRouter, HTTPException, Depends, Response, Request, Cookie
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from model.db import SessionLocal, User, init_db
import os
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from threading import Lock
from fastapi.responses import JSONResponse
import sentry_sdk
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import status
import redis
import pyotp
from cryptography.fernet import Fernet, InvalidToken
import base64

router = APIRouter()

# JWT config
SECRET_KEY = os.environ.get("MAZGPT_SECRET_KEY", "mazgpt-dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- Redis-based JWT denylist for revoked tokens ---
REDIS_DENYLIST_PREFIX = "jwt:revoked:"
REDIS_URL = os.environ.get("MAZGPT_REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# --- 2FA/MFA support ---
FERNET_KEY = os.environ.get("MAZGPT_2FA_ENC_KEY")
if not FERNET_KEY:
    # Generate a key for dev if not set (should be set in prod!)
    FERNET_KEY = base64.urlsafe_b64encode(os.urandom(32))
fernet = Fernet(FERNET_KEY)

init_db()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- get_current_user dependency (must be defined before use) ---
from fastapi import Request

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    payload = verify_token(token) if token else None
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    picture: Optional[str] = None
    tier: str = "Free"

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def revoke_jti(jti: str, exp: int):
    if jti:
        ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
        redis_client.setex(f"{REDIS_DENYLIST_PREFIX}{jti}", ttl, "1")

def is_jti_revoked(jti: str) -> bool:
    return bool(jti and redis_client.exists(f"{REDIS_DENYLIST_PREFIX}{jti}"))

# --- Token creation helpers ---
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": jti, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    to_encode = data.copy()
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": jti, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Token verification with Redis denylist check ---
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti and is_jti_revoked(jti):
            return None
        return payload
    except JWTError:
        return None

# Middleware for JWT auth
class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("access_token")
        if token:
            payload = verify_token(token)
            if payload:
                request.state.user = payload
            else:
                request.state.user = None
        else:
            request.state.user = None
        response = await call_next(request)
        return response

# Add middleware to app (in __init__.py)
# app.add_middleware(JWTAuthMiddleware)

# --- Improved input validation for login/signup/reset endpoints ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Auth endpoints
@router.post("/signup")
def signup(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Explicit CSRF check for POST (if present)
    if request.method == "POST":
        cookie_token = request.cookies.get("mazgpt-csrf")
        header_token = request.headers.get("x-csrf-token")
        if not cookie_token or not header_token or cookie_token != header_token:
            raise HTTPException(status_code=400, detail="CSRF token missing or invalid")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    db_user = User(email=user.email, name=user.name, password_hash=get_password_hash(user.password), picture=user.picture, tier=user.tier)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"ok": True}

@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.twofa_enabled:
        # Do not issue tokens yet, require 2FA verification
        return {"ok": False, "2fa_required": True, "type": user.twofa_type, "email": user.email}
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=15*60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=7*24*60*60)
    return {"ok": True, "user": {"email": user.email, "name": user.name, "picture": user.picture, "tier": user.tier}}

# --- Logout endpoint: revoke tokens ---
@router.post("/logout")
def logout(request: Request, response: Response):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    for token in (access_token, refresh_token):
        payload = verify_token(token) if token else None
        jti = payload.get("jti") if payload else None
        exp = int(payload.get("exp", 0)) if payload else 0
        if jti and exp:
            revoke_jti(jti, exp)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"ok": True}

@router.post("/reset-password")
def reset_password(email: EmailStr, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    # TODO: Send reset email (stub)
    return {"ok": True}

@router.get("/profile")
def get_profile(email: EmailStr, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": user.email, "name": user.name, "picture": user.picture, "tier": user.tier}

@router.post("/change-password")
def change_password(email: EmailStr, old_password: str, new_password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(old_password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return {"ok": True}

@router.post("/refresh-token")
def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    payload = verify_token(token) if token else None
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    email = payload.get("sub")
    access_token = create_access_token({"sub": email})
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60)
    return {"ok": True}

# --- 2FA support endpoints ---
def encrypt_2fa_secret(secret: str) -> str:
    return fernet.encrypt(secret.encode()).decode()

def decrypt_2fa_secret(enc: str) -> str:
    try:
        return fernet.decrypt(enc.encode()).decode()
    except (InvalidToken, Exception):
        return None

class TwoFAEnableRequest(BaseModel):
    type: str  # 'totp' or 'email'

class TwoFAVerifyRequest(BaseModel):
    code: str
    type: Optional[str] = None  # 'totp' or 'email', optional for login
    email: Optional[EmailStr] = None  # for login

@router.post("/2fa/enable")
def enable_2fa(req: TwoFAEnableRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.type == "totp":
        secret = pyotp.random_base32()
        secret_enc = encrypt_2fa_secret(secret)
        current_user.twofa_enabled = True
        current_user.twofa_type = "totp"
        current_user.twofa_secret_enc = secret_enc
        db.commit()
        # Generate otpauth URL for authenticator apps
        otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="MazGPT")
        return {"ok": True, "type": "totp", "otpauth_url": otpauth_url, "secret": secret}
    elif req.type == "email":
        import random
        code = f"{random.randint(100000, 999999)}"
        current_user.twofa_enabled = True
        current_user.twofa_type = "email"
        current_user.twofa_email_code = code
        current_user.twofa_email_code_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        # TODO: Send code via email (stub)
        print(f"[2FA EMAIL] Send code {code} to {current_user.email}")
        return {"ok": True, "type": "email"}
    else:
        raise HTTPException(status_code=400, detail="Invalid 2FA type")

@router.post("/2fa/verify")
def verify_2fa(req: TwoFAVerifyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.twofa_type == "totp":
        secret = decrypt_2fa_secret(current_user.twofa_secret_enc)
        if not secret:
            raise HTTPException(status_code=400, detail="2FA secret error")
        totp = pyotp.TOTP(secret)
        if not totp.verify(req.code, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")
        return {"ok": True}
    elif current_user.twofa_type == "email":
        if (current_user.twofa_email_code != req.code or
            not current_user.twofa_email_code_expiry or
            datetime.now(timezone.utc) > current_user.twofa_email_code_expiry):
            raise HTTPException(status_code=401, detail="Invalid or expired 2FA code")
        # Invalidate code after use
        current_user.twofa_email_code = None
        current_user.twofa_email_code_expiry = None
        db.commit()
        return {"ok": True}
    else:
        raise HTTPException(status_code=400, detail="2FA not enabled")

@router.post("/2fa/disable")
def disable_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.twofa_enabled = False
    current_user.twofa_type = None
    current_user.twofa_secret_enc = None
    current_user.twofa_email_code = None
    current_user.twofa_email_code_expiry = None
    db.commit()
    return {"ok": True}

@router.get("/2fa/status")
def twofa_status(current_user: User = Depends(get_current_user)):
    return {"enabled": current_user.twofa_enabled, "type": current_user.twofa_type}

# --- 2FA login verification endpoint ---
class TwoFALoginVerifyRequest(BaseModel):
    email: EmailStr
    code: str
    type: Optional[str] = None

@router.post("/2fa/login-verify")
def twofa_login_verify(req: TwoFALoginVerifyRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.twofa_enabled:
        raise HTTPException(status_code=401, detail="2FA not enabled for this user")
    if user.twofa_type == "totp":
        secret = decrypt_2fa_secret(user.twofa_secret_enc)
        if not secret:
            raise HTTPException(status_code=400, detail="2FA secret error")
        totp = pyotp.TOTP(secret)
        if not totp.verify(req.code, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")
    elif user.twofa_type == "email":
        if (user.twofa_email_code != req.code or
            not user.twofa_email_code_expiry or
            datetime.now(timezone.utc) > user.twofa_email_code_expiry):
            raise HTTPException(status_code=401, detail="Invalid or expired 2FA code")
        # Invalidate code after use
        user.twofa_email_code = None
        user.twofa_email_code_expiry = None
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    # On success, issue tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=15*60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=7*24*60*60)
    return {"ok": True, "user": {"email": user.email, "name": user.name, "picture": user.picture, "tier": user.tier}}

# --- Global error handler for safe messages and Sentry reporting ---
def setup_error_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        sentry_sdk.capture_exception(exc)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail if exc.status_code < 500 else "Internal server error"})

    @app.exception_handler(FastAPIRequestValidationError)
    async def validation_exception_handler(request, exc):
        sentry_sdk.capture_exception(exc)
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "Invalid input"})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        sentry_sdk.capture_exception(exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
