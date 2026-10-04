"""Эндпоинты авторизации."""
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.auth import (
    DEMO_PASSWORD,
    DEMO_USERNAME,
    create_session,
    destroy_session,
    get_current_user,
)
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response) -> LoginResponse:
    """Проверяет логин/пароль, ставит куку сессии."""
    if payload.username != DEMO_USERNAME or payload.password != DEMO_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    session_id = create_session(payload.username)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return LoginResponse(username=payload.username)


@router.post("/logout")
async def logout(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None,
) -> dict:
    if session_id is not None:
        destroy_session(session_id)
    response.delete_cookie("session_id")
    return {"message": "logged out"}


@router.get("/me")
async def me(current_user: Annotated[str, Depends(get_current_user)]) -> dict:
    return {"username": current_user}