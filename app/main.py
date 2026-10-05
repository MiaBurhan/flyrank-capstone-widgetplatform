"""App entrypoint: wires config, middleware, error handling and routers together."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, pages, public
from app.config import get_settings
from app.database import init_db
from app.errors import AppError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Embeddable Widget & Lead-Capture Platform", lifespan=lifespan)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def guard_and_harden(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > settings.max_body_bytes:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# Customer sites live on other origins, so the browser needs CORS to be open.
# Real access control is the per-widget allowed_origins check in the service layer
# and the admin key on /admin (header based, no cookies, so no CSRF surface).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

app.include_router(public.router)
app.include_router(admin.router)
app.include_router(pages.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
