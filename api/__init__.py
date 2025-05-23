# FastAPI API entrypoint for MazGPT user/account features
from fastapi import FastAPI
from .auth import router as auth_router
from .user_data import router as user_data_router
from .settings import router as settings_router
from .auth import JWTAuthMiddleware
from .chat import router as chat_router
from .project import router as project_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import time
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from .csrf import CSRFMiddleware
from .auth import setup_error_handlers
import os

# --- Sentry error reporting ---
SENTRY_DSN = os.environ.get("SENTRY_DSN", "YOUR_SENTRY_DSN")
if SENTRY_DSN and SENTRY_DSN != "YOUR_SENTRY_DSN":
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=1.0)

# --- Rate limiting ---
limiter = Limiter(key_func=get_remote_address)

# --- Security headers middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

app = FastAPI()
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
if not os.environ.get("TESTING"):
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}))
app.state.limiter = limiter
app.add_middleware(SentryAsgiMiddleware)
app.add_middleware(CSRFMiddleware)

# --- Audit logging middleware ---
class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        user = request.headers.get("Authorization", "anonymous")
        print(f"AUDIT {request.method} {request.url.path} user={user} status={response.status_code} time={duration:.3f}s")
        return response
app.add_middleware(AuditLoggingMiddleware)

setup_error_handlers(app)

app.include_router(auth_router, prefix="/auth")
app.include_router(user_data_router, prefix="/user")
app.include_router(settings_router, prefix="/user")
app.include_router(chat_router, prefix="/chat")
app.include_router(project_router, prefix="/project")

@app.get("/ping")
def ping(request):
    # Set CSRF cookie if not present
    response = Response(content="pong", media_type="text/plain")
    if not request.cookies.get("mazgpt-csrf"):
        import secrets
        token = secrets.token_urlsafe(32)
        secure_flag = not bool(os.environ.get("TESTING"))
        response.set_cookie(
            "mazgpt-csrf", token, httponly=False, secure=secure_flag, max_age=60*60*8, samesite="Lax"
        )
    return response

# Restore temporary test helper routes for trailing slashes
from api.project import list_projects
app.add_api_route("/project/list/", list_projects, methods=["GET"])
from api.chat import send_chat
app.add_api_route("/chat/send/", send_chat, methods=["POST"])
