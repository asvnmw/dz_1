from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Движок — объект, через который SQLAlchemy общается с PostgreSQL.
engine = create_async_engine(
    settings.database_url,
    echo=False,   # True — печатать все SQL-запросы в консоль (удобно при отладке)
    future=True,
)


# Фабрика сессий. Каждый запрос к API будет создавать свою сессию.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Базовый класс для всех моделей (таблиц).
class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()