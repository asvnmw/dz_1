"""Pydantic-схемы для валидации запросов и сериализации ответов."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# читатель

class ReaderBase(BaseModel):
    full_name: str = Field(..., max_length=200)
    card_number: str = Field(..., max_length=50)
    email: str | None = None
    phone: str | None = None


class ReaderCreate(ReaderBase):
    pass


class ReaderOut(ReaderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# книга

class BookBase(BaseModel):
    title: str = Field(..., max_length=300)
    author: str = Field(..., max_length=200)
    isbn: str | None = None
    year: int | None = None


class BookCreate(BookBase):
    pass


class BookOut(BookBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# экземпляр

class CopyBase(BaseModel):
    book_id: int
    inventory_number: str = Field(..., max_length=50)


class CopyCreate(CopyBase):
    pass


class CopyOut(CopyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_available: bool
    created_at: datetime


# выдача

class LoanCreate(BaseModel):
    reader_id: int
    copy_id: int
    due_at: date


class LoanReturn(BaseModel):
    returned_at: date


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reader_id: int
    copy_id: int
    issued_at: date
    due_at: date
    returned_at: date | None
    created_at: datetime
    is_overdue: bool
    overdue_days: int
    fine_amount: Decimal


class PaginatedLoans(BaseModel):
    items: list[LoanOut]
    total: int
    page: int
    size: int


# сводка

class SummaryOut(BaseModel):
    total_loans: int
    active_loans: int
    overdue_loans: int
    top_books: list[dict]


# авторизация

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    message: str = "ok"