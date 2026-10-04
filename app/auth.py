"""Простая сессионная авторизация в памяти процесса."""
import secrets
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo"

_sessions: dict[str, str] = {}


def create_session(username: str) -> str:
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = username
    return session_id


def destroy_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def get_current_user(
    session_id: Annotated[str | None, Cookie()] = None,
) -> str:
    if session_id is None or session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
        )
    return _sessions[session_id]