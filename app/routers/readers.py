"""Эндпоинты для работы с читателями."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import Reader
from app.schemas import ReaderOut

router = APIRouter(prefix="/api/readers", tags=["readers"])


@router.get("", response_model=dict)
async def list_readers(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> dict:
    """Список читателей с поиском по ФИО и постраничным выводом."""
    stmt = select(Reader)
    count_stmt = select(func.count(Reader.id))

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Reader.full_name.ilike(pattern))
        count_stmt = count_stmt.where(Reader.full_name.ilike(pattern))

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Reader.id).offset((page - 1) * size).limit(size)
    readers = (await session.execute(stmt)).scalars().all()

    return {
        "items": [ReaderOut.model_validate(r) for r in readers],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{reader_id}", response_model=ReaderOut)
async def get_reader(
    reader_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> ReaderOut:
    """Карточка читателя."""
    reader = await session.get(Reader, reader_id)
    if reader is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Читатель не найден",
        )
    return ReaderOut.model_validate(reader)