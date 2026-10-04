"""Тесты операций программного интерфейса.

Проверяют коды ответов и поведение без авторизации.
Тесты, требующие реальной БД, вынесены в test_rules.py (там проверяется логика).
"""
import pytest
from httpx import AsyncClient

from app.auth import create_session, destroy_session


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Успешный логин возвращает 200 и имя пользователя."""
    resp = await client.post(
        "/auth/login",
        json={"username": "demo", "password": "demo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "demo"
    assert "session_id" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Неверный пароль возвращает 401."""
    resp = await client.post(
        "/auth/login",
        json={"username": "demo", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_loans_list_requires_auth(client: AsyncClient):
    """Без авторизации список выдач возвращает 401."""
    resp = await client.get("/api/loans")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_loan_detail_requires_auth(client: AsyncClient):
    """Без авторизации карточка выдачи возвращает 401."""
    resp = await client.get("/api/loans/1")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_loan_requires_auth(client: AsyncClient):
    """Без авторизации создание выдачи возвращает 401."""
    resp = await client.post(
        "/api/loans",
        json={"reader_id": 1, "copy_id": 1, "due_at": "2026-12-31"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_return_loan_requires_auth(client: AsyncClient):
    """Без авторизации возврат книги возвращает 401."""
    resp = await client.post(
        "/api/loans/1/return",
        json={"returned_at": "2026-12-31"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_summary_requires_auth(client: AsyncClient):
    """Без авторизации сводка возвращает 401."""
    resp = await client.get("/api/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_readers_requires_auth(client: AsyncClient):
    """Без авторизации список читателей возвращает 401."""
    resp = await client.get("/api/readers")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_books_requires_auth(client: AsyncClient):
    """Без авторизации список книг возвращает 401."""
    resp = await client.get("/api/books")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_then_me(client: AsyncClient):
    """После логина /auth/me возвращает имя пользователя."""
    session_id = create_session("demo")
    try:
        resp = await client.get(
            "/auth/me",
            cookies={"session_id": session_id},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "demo"
    finally:
        destroy_session(session_id)


@pytest.mark.asyncio
async def test_me_without_auth(client: AsyncClient):
    """Без авторизации /auth/me возвращает 401."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401