"""FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wf_catalogue_service.api.health.routes import health_router
from wf_catalogue_service.api.v1.workflows.routes import register_router, workflow_router
from wf_catalogue_service.core.settings import current_settings

settings = current_settings()


def create_api_v1(parent_app: FastAPI) -> FastAPI:
    """Create and register API v1 sub-application."""
    sub_app = FastAPI(
        title="EODH Workflow Catalogue API",
        version="1.0.0",
        description="Workflow Catalogue Service API.",
        debug=settings.environment.lower() in {"local", "dev"},
        openapi_url=None if settings.environment.lower() == "prod" else "/openapi.json",
    )
    sub_app.include_router(health_router)
    sub_app.include_router(workflow_router)
    sub_app.include_router(register_router)
    parent_app.mount("/api/v1.0", sub_app)
    return sub_app


app = FastAPI(
    title="EODH Workflow Catalogue API",
    version="1.0.0",
    description="Workflow Catalogue Service API.",
    docs_url=None,
    debug=settings.environment.lower() in {"local", "dev"},
)

app_v1 = create_api_v1(app)
app.mount("/api/latest", app_v1)
app.mount("/api/v1.0", app_v1)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
