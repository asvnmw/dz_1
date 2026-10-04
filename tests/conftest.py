"""Общие фикстуры pytest для всех тестов."""
import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import _sessions, create_session
from app.database import AsyncSessionLocal
from main import app  # noqa: F401 — просто чтобы FastAPI инициализировался


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Открывает сессию БД для теста и закрывает после."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент, работающий с приложением в памяти (без реального порта)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_cookie() -> str:
    """Создаёт тестовую сессию и возвращает её session_id (без HTTP)."""
    session_id = create_session("demo")
    yield session_id
    _sessions.pop(session_id, None)