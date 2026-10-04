from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reader(Base):
    """Читатель библиотеки."""
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    card_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связь: у читателя много выдач.
    loans: Mapped[list["Loan"]] = relationship(back_populates="reader")


class Book(Base):
    """Книга (произведение) — метаданные."""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связь: у книги много экземпляров.
    copies: Mapped[list["Copy"]] = relationship(back_populates="book")


class Copy(Base):
    """Физический экземпляр книги."""
    __tablename__ = "copies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("books.id"), nullable=False
    )
    inventory_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    is_available: Mapped[bool] = mapped_column(
        default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи.
    book: Mapped["Book"] = relationship(back_populates="copies")
    loans: Mapped[list["Loan"]] = relationship(back_populates="copy")


class Loan(Base):
    """Выдача экземпляра читателю. Основная операционная таблица."""
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reader_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("readers.id"), nullable=False
    )
    copy_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("copies.id"), nullable=False
    )
    issued_at: Mapped[date] = mapped_column(Date, nullable=False)
    due_at: Mapped[date] = mapped_column(Date, nullable=False)
    returned_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи.
    reader: Mapped["Reader"] = relationship(back_populates="loans")
    copy: Mapped["Copy"] = relationship(back_populates="loans")

    # Бизнес-правила (в Python, не в БД).
    @property
    def is_overdue(self) -> bool:
        """Просрочена ли выдача."""
        end_date = self.returned_at or date.today()
        return end_date > self.due_at

    @property
    def overdue_days(self) -> int:
        """Число дней просрочки."""
        if not self.is_overdue:
            return 0
        end_date = self.returned_at or date.today()
        return (end_date - self.due_at).days

    @property
    def fine_amount(self) -> Decimal:
        """Штраф: 10 рублей за каждый день просрочки."""
        return Decimal(self.overdue_days) * Decimal("10.00")