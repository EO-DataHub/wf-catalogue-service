"""FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wf_catalogue_service.api.health.routes import health_router
from wf_catalogue_service.api.v1.workflows.routes import workflow_router
from wf_catalogue_service.core.settings import current_settings

settings = current_settings()


app = FastAPI(
    title="EODH Workflow Catalogue API",
    version="1.0.0",
    description="Workflow Catalogue Service API.",
    debug=settings.environment.lower() in {"local", "dev"},
    openapi_url=None if settings.environment.lower() == "prod" else "/openapi.json",
)

app.include_router(health_router)
app.include_router(workflow_router)

app.mount("/api/latest", app)
app.mount("/api/v1.0", app)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
