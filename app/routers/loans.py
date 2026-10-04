"""Эндпоинты для работы с выдачами книг."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import Copy, Loan
from app.schemas import LoanCreate, LoanOut, LoanReturn, PaginatedLoans

router = APIRouter(prefix="/api/loans", tags=["loans"])


@router.get("", response_model=PaginatedLoans)
async def list_loans(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    reader_id: int | None = None,
    only_active: bool = False,
) -> PaginatedLoans:
    """Список выдач с фильтром и постраничным выводом."""
    stmt = select(Loan)
    count_stmt = select(func.count(Loan.id))

    if reader_id is not None:
        stmt = stmt.where(Loan.reader_id == reader_id)
        count_stmt = count_stmt.where(Loan.reader_id == reader_id)

    if only_active:
        stmt = stmt.where(Loan.returned_at.is_(None))
        count_stmt = count_stmt.where(Loan.returned_at.is_(None))

    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Loan.id).offset((page - 1) * size).limit(size)
    loans = (await session.execute(stmt)).scalars().all()

    return PaginatedLoans(
        items=[LoanOut.model_validate(loan) for loan in loans],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{loan_id}", response_model=LoanOut)
async def get_loan(
    loan_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> LoanOut:
    """Карточка выдачи со связанными сущностями."""
    loan = await session.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Выдача не найдена",
        )
    return LoanOut.model_validate(loan)


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
async def create_loan(
    payload: LoanCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> LoanOut:
    """Выдаёт экземпляр читателю.

    Правила:
    - экземпляр должен существовать и быть свободен;
    - у читателя не должно быть просроченных выдач.
    """
    copy = await session.get(Copy, payload.copy_id)
    if copy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Экземпляр не найден",
        )
    if not copy.is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Экземпляр уже выдан",
        )

    overdue_stmt = (
        select(Loan)
        .where(Loan.reader_id == payload.reader_id)
        .where(Loan.returned_at.is_(None))
        .where(Loan.due_at < date.today())
    )
    overdue = (await session.execute(overdue_stmt)).scalars().first()
    if overdue is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У читателя есть просроченные выдачи",
        )

    loan = Loan(
        reader_id=payload.reader_id,
        copy_id=payload.copy_id,
        issued_at=date.today(),
        due_at=payload.due_at,
        returned_at=None,
    )
    copy.is_available = False
    session.add(loan)
    await session.commit()
    await session.refresh(loan)

    return LoanOut.model_validate(loan)


@router.post("/{loan_id}/return", response_model=LoanOut)
async def return_loan(
    loan_id: int,
    payload: LoanReturn,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> LoanOut:
    """Принимает возврат книги с фиксацией даты."""
    loan = await session.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Выдача не найдена",
        )
    if loan.returned_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Книга уже возвращена",
        )

    loan.returned_at = payload.returned_at

    copy = await session.get(Copy, loan.copy_id)
    if copy is not None:
        copy.is_available = True

    await session.commit()
    await session.refresh(loan)

    return LoanOut.model_validate(loan)