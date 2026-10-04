"""Эндпоинт сводки по всей библиотеке."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import Book, Copy, Loan
from app.schemas import SummaryOut

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("", response_model=SummaryOut)
async def get_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> SummaryOut:
    """Сводка: всего выдач, активных, просроченных, топ книг."""
    total_loans = (await session.execute(select(func.count(Loan.id)))).scalar_one()

    active_loans = (
        await session.execute(
            select(func.count(Loan.id)).where(Loan.returned_at.is_(None))
        )
    ).scalar_one()

    today = date.today()
    overdue_loans = (
        await session.execute(
            select(func.count(Loan.id))
            .where(Loan.returned_at.is_(None))
            .where(Loan.due_at < today)
        )
    ).scalar_one()

    # Топ-10 книг по числу выдач.
    top_stmt = (
        select(Book.id, Book.title, func.count(Loan.id).label("loan_count"))
        .join(Copy, Copy.book_id == Book.id)
        .join(Loan, Loan.copy_id == Copy.id)
        .group_by(Book.id, Book.title)
        .order_by(func.count(Loan.id).desc())
        .limit(10)
    )
    top_rows = (await session.execute(top_stmt)).all()
    top_books = [
        {"book_id": row[0], "title": row[1], "loan_count": row[2]}
        for row in top_rows
    ]

    return SummaryOut(
        total_loans=total_loans,
        active_loans=active_loans,
        overdue_loans=overdue_loans,
        top_books=top_books,
    )