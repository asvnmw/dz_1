"""Эндпоинты для работы с книгами и экземплярами."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import Book, Copy
from app.schemas import BookOut, CopyOut

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("", response_model=dict)
async def list_books(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> dict:
    """Список книг с поиском по названию или автору и постраничным выводом."""
    stmt = select(Book)
    count_stmt = select(func.count(Book.id))

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where((Book.title.ilike(pattern)) | (Book.author.ilike(pattern)))
        count_stmt = count_stmt.where((Book.title.ilike(pattern)) | (Book.author.ilike(pattern)))

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Book.id).offset((page - 1) * size).limit(size)
    books = (await session.execute(stmt)).scalars().all()

    return {
        "items": [BookOut.model_validate(b) for b in books],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{book_id}", response_model=dict)
async def get_book(
    book_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> dict:
    """Карточка книги с экземплярами."""
    book = await session.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )

    copies_stmt = select(Copy).where(Copy.book_id == book_id).order_by(Copy.id)
    copies = (await session.execute(copies_stmt)).scalars().all()

    return {
        "book": BookOut.model_validate(book),
        "copies": [CopyOut.model_validate(c) for c in copies],
    }