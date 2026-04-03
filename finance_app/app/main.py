from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import Base, engine
from . import models  # noqa: F401 (ensures models are registered)
from .routes.auth import router as auth_router
from .routes.transactions import router as transactions_router
from .utils.logging_config import configure_logging
from .utils.responses import api_response


def create_app() -> FastAPI:
    """
    Application factory.

    Keeping app creation in a function makes it easier to
    test and to plug in different configurations later.
    """
    app = FastAPI(
        title="Finance Tracking System Backend",
        description="Simple but professional finance tracking API built with FastAPI.",
        version="0.1.0",
    )

    configure_logging()

    # CORS is helpful for local frontend development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        # For a small demo project, auto-create tables on startup.
        # In production, prefer migrations (e.g., Alembic).
        Base.metadata.create_all(bind=engine)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Wrap FastAPI HTTP errors in our standard response envelope.
        return JSONResponse(
            status_code=exc.status_code,
            content=api_response(False, str(exc.detail), None),
            headers=getattr(exc, "headers", None),
        )

    @app.get("/health")
    async def health_check():
        return api_response(True, "OK", None)

    app.include_router(auth_router)
    app.include_router(transactions_router)

    return app


app = create_app()

