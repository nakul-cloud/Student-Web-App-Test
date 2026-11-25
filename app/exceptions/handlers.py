"""Global exception handlers for FastAPI."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.custom_exceptions import AppError
from app.utils.logger import logger


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.error(f"AppError: {exc.message}")
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.message})


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"success": False, "message": "Validation error", "errors": exc.errors()})


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"success": False, "message": "Internal server error"})
