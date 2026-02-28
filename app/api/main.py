"""FastAPI application factory — creates and configures the app.

Usage:
    uvicorn app.api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, pipelines, workspaces
from app.config import get_settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="Affiliate Ad Agency API",
        version="0.2.0",
        description="AI-powered affiliate ad agency — REST API",
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url="/redoc" if settings.app_env != "prod" else None,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "dev" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(health.router)
    application.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    application.include_router(
        workspaces.router,
        prefix="/api/workspaces",
        tags=["workspaces"],
    )
    application.include_router(
        pipelines.router,
        prefix="/api/pipelines",
        tags=["pipelines"],
    )

    return application


# Module-level app instance for uvicorn
app = create_app()
