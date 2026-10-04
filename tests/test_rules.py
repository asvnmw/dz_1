"""Тесты бизнес-правил предметной области «Выдача книг в библиотеке»."""
from datetime import date, timedelta
from decimal import Decimal

from app.models import Loan


def test_loan_not_overdue_when_returned_before_due():
    """Если книга возвращена до срока — просрочки нет."""
    loan = Loan(
        reader_id=1,
        copy_id=1,
        issued_at=date(2026, 1, 1),
        due_at=date(2026, 1, 15),
        returned_at=date(2026, 1, 10),
    )
    assert loan.is_overdue is False
    assert loan.overdue_days == 0
    assert loan.fine_amount == Decimal("0.00")


def test_loan_overdue_when_returned_after_due():
    """Если книга возвращена после срока — просрочка считается по дням."""
    loan = Loan(
        reader_id=1,
        copy_id=1,
        issued_at=date(2026, 1, 1),
        due_at=date(2026, 1, 15),
        returned_at=date(2026, 1, 20),
    )
    assert loan.is_overdue is True
    assert loan.overdue_days == 5
    assert loan.fine_amount == Decimal("50.00")


def test_loan_overdue_when_not_returned_and_due_in_past():
    """Если книга на руках и срок прошёл — просрочка считается от сегодня."""
    today = date.today()
    loan = Loan(
        reader_id=1,
        copy_id=1,
        issued_at=today - timedelta(days=30),
        due_at=today - timedelta(days=10),
        returned_at=None,
    )
    assert loan.is_overdue is True
    assert loan.overdue_days == 10
    assert loan.fine_amount == Decimal("100.00")


def test_loan_not_overdue_on_exact_due_date():
    """Возврат ровно в срок — просрочки нет."""
    loan = Loan(
        reader_id=1,
        copy_id=1,
        issued_at=date(2026, 1, 1),
        due_at=date(2026, 1, 15),
        returned_at=date(2026, 1, 15),
    )
    assert loan.is_overdue is False
    assert loan.overdue_days == 0


def test_fine_amount_is_ten_per_day():
    """Штраф — 10 рублей за каждый день просрочки."""
    loan = Loan(
        reader_id=1,
        copy_id=1,
        issued_at=date(2026, 1, 1),
        due_at=date(2026, 1, 15),
        returned_at=date(2026, 1, 25),
    )
    # 10 дней просрочки * 10 руб./день = 100 руб.
    assert loan.fine_amount == Decimal("100.00")


def test_fine_amount_zero_for_short_loan():
    """Если книга возвращена вовремя, штраф — ноль."""
    loan = Loan(
        reader_id=1,
        copy_id=1,
        issued_at=date(2026, 1, 1),
        due_at=date(2026, 1, 15),
        returned_at=date(2026, 1, 14),
    )
    assert loan.fine_amount == Decimal("0.00")