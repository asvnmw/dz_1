"""Создаёт все таблицы в базе. Запускать один раз после настройки .env."""
import asyncio

from app.database import Base, engine
from app import models  # noqa: F401 — важно, чтобы SQLAlchemy увидела модели


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы созданы.")


if __name__ == "__main__":
    asyncio.run(main())