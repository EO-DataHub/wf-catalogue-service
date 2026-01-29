"""Test configuration and fixtures."""

from __future__ import annotations

import json
import os
import pathlib
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wf_catalogue_service import consts
from wf_catalogue_service.db.models import Base, Catalogue
from wf_catalogue_service.db.session import get_session
from wf_catalogue_service.main import app_v1

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from _pytest.config import Config
    from _pytest.python import Function

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://catalogue:catalogue_dev_password@localhost:5432/workflow_catalogue",
)
FIXTURES_PATH = pathlib.Path(__file__).parent / "fixtures"


def pytest_collection_modifyitems(config: Config, items: list[Function]) -> None:  # noqa: ARG001
    """Add markers based on test directory."""
    rootdir = pathlib.Path(consts.directories.ROOT_DIR)
    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir)
        mark_name = rel_path.as_posix().split("/")[1]
        mark = getattr(pytest.mark, mark_name)
        item.add_marker(mark)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Create async test client with test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        catalogue = Catalogue(
            id="eodh-workflows-notebooks",
            type="Collection",
            item_type="record",
            title="EODH Workflows and Notebooks Catalog",
            description="Test catalogue",
            keywords=["test"],
            language="en",
            license="proprietary",
        )
        session.add(catalogue)
        await session.commit()

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    app_v1.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app_v1), base_url="http://test") as ac:
        yield ac

    app_v1.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def workflow_json() -> Any:
    """Load workflow JSON fixture."""
    with (FIXTURES_PATH / "ndvi-workflow.json").open() as f:
        return json.load(f)


@pytest.fixture
def notebook_json() -> Any:
    """Load notebook JSON fixture."""
    with (FIXTURES_PATH / "ndvi-notebook.json").open() as f:
        return json.load(f)
