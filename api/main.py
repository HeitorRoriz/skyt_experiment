# api/main.py
"""
SKYT API - Main Application

FastAPI application entry point for the SKYT SaaS platform.

Usage:
    uvicorn api.main:app --reload
    
    Or with custom host/port:
    uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import health, pipeline, jobs, contracts, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🚀 Starting SKYT API v{settings.api_version}")
    print(f"   Debug mode: {settings.debug}")
    print(f"   API prefix: {settings.api_prefix}")
    yield
    # Shutdown
    print("👋 Shutting down SKYT API")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="""
# SKYT API

**Software Repeatability as a Service**

SKYT provides a contract-based harness for evaluating and enforcing
code repeatability in LLM-assisted development.

## Features

- 📋 **Contracts**: Define code generation requirements with oracles
- 🔒 **Restrictions**: Apply certification standards (NASA, MISRA, DO-178C)
- 📊 **Metrics**: Measure repeatability (R_raw, R_anchor, Δ_rescue)
- ⚡ **Real-time**: WebSocket updates for job progress

## Authentication

Most endpoints require JWT authentication. Get a token via `POST /api/v1/auth/token`.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix=settings.api_prefix, tags=["Authentication"])
    app.include_router(pipeline.router, prefix=settings.api_prefix, tags=["Pipeline"])
    app.include_router(jobs.router, prefix=settings.api_prefix, tags=["Jobs"])
    app.include_router(contracts.router, prefix=settings.api_prefix, tags=["Contracts"])
    
    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
