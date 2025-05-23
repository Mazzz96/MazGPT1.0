# api/csrf.py
# Simple CSRF protection middleware for FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import secrets
import time
import os

CSRF_COOKIE_NAME = "mazgpt-csrf"
CSRF_HEADER_NAME = "x-csrf-token"
CSRF_TOKEN_TTL = 60 * 60 * 8  # 8 hours

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only protect state-changing methods
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)
            if not cookie_token or not header_token or cookie_token != header_token:
                return JSONResponse(status_code=403, content={"detail": "CSRF token missing or invalid"})
        # Issue CSRF token if not present (on GET, HEAD, OPTIONS)
        response: Response = await call_next(request)
        if request.method in ("GET", "HEAD", "OPTIONS"):
            if not request.cookies.get(CSRF_COOKIE_NAME):
                token = secrets.token_urlsafe(32)
                secure_flag = not bool(os.environ.get("TESTING"))
                response.set_cookie(
                    CSRF_COOKIE_NAME, token, httponly=False, secure=secure_flag, max_age=CSRF_TOKEN_TTL, samesite="Lax"
                )
        return response
