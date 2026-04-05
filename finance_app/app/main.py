import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import Base, engine
from . import models  # noqa: F401 (ensures models are registered)
from .routes.auth import router as auth_router
from .routes.transactions import router as transactions_router
from .utils.logging_config import configure_logging
from .utils.responses import api_response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Finance Tracking System Backend",
        description="Simple but professional finance tracking API built with FastAPI.",
        version="0.1.0",
    )

    # CORS configuration
    cors_origins = os.getenv("ALLOWED_ORIGINS", "*")
    if cors_origins == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [origin.strip() for origin in cors_origins.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True if cors_origins != "*" else False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=api_response(False, str(exc.detail), None),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = error["loc"][-1] if error["loc"] else "unknown"
            error_type = error["type"]
            
            if error_type == "string_too_long":
                max_length = error.get("ctx", {}).get("max_length")
                message = f"{field} must not exceed {max_length} characters"
            elif error_type == "string_too_short":
                min_length = error.get("ctx", {}).get("min_length")
                message = f"{field} must have at least {min_length} characters"
            elif error_type == "value_error":
                message = f"Invalid value for {field}: {error['msg']}"
            elif error_type == "type_error":
                message = f"{field} has invalid type. Please check the format"
            elif error_type == "json_invalid":
                message = "Invalid input from user"
            elif error_type == "json_schema_validation_error":
                message = f"Invalid data for {field}: {error['msg']}"
            else:
                message = f"Invalid {field}: {error['msg']}"
            
            errors.append(message)
        
        return JSONResponse(
            status_code=422,
            content=api_response(False, "Validation error", errors if len(errors) > 1 else (errors[0] if errors else "Invalid request")),
        )

    @app.get("/health")
    async def health_check():
        return api_response(True, "OK", None)

    app.include_router(auth_router)
    app.include_router(transactions_router)

    return app


app = create_app()

