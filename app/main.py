import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings
from app.config.database import engine, Base
from app.config.redis import get_redis, close_redis
from app.providers.qdrant_provider import get_qdrant_client, close_qdrant_client
from app.services.ingestion_service import seed_qdrant_faqs
from app.utils.limiter import limiter
from app.exceptions.custom_exceptions import AppError
from app.exceptions.handlers import (
    app_error_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.routes.index import api_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in {settings.env} mode...")

    # 1. Initialize PostgreSQL tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[Startup] PostgreSQL tables verified.")
    except Exception as e:
        logger.error(f"[Startup] PostgreSQL init error: {e}")

    # 2. Verify Redis pool
    try:
        r = await get_redis()
        logger.info("[Startup] Redis connection established.")
    except Exception as e:
        logger.error(f"[Startup] Redis connection error: {e}")

    # 3. Seed Vectorless Qdrant FAQs
    try:
        count = await seed_qdrant_faqs()
        logger.info(f"[Startup] Qdrant knowledge base loaded with {count} FAQs.")
    except Exception as e:
        logger.error(f"[Startup] Qdrant seeding warning: {e}")

    yield

    # Shutdown
    logger.info("Shutting down ComplyADI...")
    await close_redis()
    await close_qdrant_client()
    await engine.dispose()
    logger.info("Connections disposed.")


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    docs_url="/docs" if settings.env == "development" else None,
    redoc_url="/redoc" if settings.env == "development" else None,
    openapi_url="/openapi.json" if settings.env == "development" else None,
    lifespan=lifespan,
)

app.state.limiter = limiter

# Request timing & audit logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    # Don't clutter logs with static asset queries
    if not request.url.path.startswith("/frontend"):
        logger.info(f"[HTTP] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response

# Compression & CORS
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.env == "production" else ["*"],
    allow_credentials=True if settings.env == "production" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Mount Routes
app.include_router(api_router, prefix="/api/v1")

# Mount Modular Frontend Static Assets
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(_FRONTEND_DIR)), name="frontend")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "ComplyADI - GIFT City Compliance Assistant",
        "chat_ui": "/api/v1/chatbot/",
        "api_docs": "/docs",
    }
