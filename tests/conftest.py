import asyncio
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database.models import Base
from app.templates.loader import TemplateLoader


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def template_loader():
    # Load templates from actual documents directory
    return TemplateLoader(templates_dir="app/templates/documents")


@pytest.fixture
def sample_usps_ocr_text():
    return """
    USPS GROUND ADVANTAGE
    UNITED STATES POSTAL SERVICE
    TRACKING NUMBER: 9748 8529 8102 9384 7561 00
    SHIP TO:
    Food Lion
    123 Main Street
    Clemmons NC 27012
    POSTAGE PAID
    """
