"""Наполнение базы данных.

Запуск:
    python -m scripts.seed small      # малое наполнение (300 выдач)
    python -m scripts.seed working    # рабочее (50 000 выдач)

Воспроизводимость: повторный запуск с тем же размером даёт тот же результат,
потому что используется фиксированный seed и предварительная очистка таблиц.
"""
import asyncio
import random
import sys
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Book, Copy, Loan, Reader


# Фиксированный seed — для воспроизводимости.
SEED = 42

# Наборы для генерации данных.
FIRST_NAMES = [
    "Иван", "Пётр", "Сергей", "Алексей", "Дмитрий",
    "Анна", "Мария", "Ольга", "Елена", "Татьяна",
    "Николай", "Владимир", "Екатерина", "Наталья", "Ирина",
]
LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов",
    "Волков", "Морозов", "Новиков", "Фёдоров", "Егоров",
    "Соколов", "Попов", "Лебедев", "Козлов", "Степанов",
]
BOOK_TITLES = [
    "Война и мир", "Преступление и наказание", "Мастер и Маргарита",
    "Тихий Дон", "Евгений Онегин", "Мёртвые души", "Отцы и дети",
    "Герой нашего времени", "Обломов", "Анна Каренина",
    "Братья Карамазовы", "Идиот", "Белая гвардия", "Собачье сердце",
    "Двенадцать стульев", "Золотой телёнок", "Три товарища",
    "1984", "Скотный двор", "О дивный новый мир",
]
BOOK_AUTHORS = [
    "Л. Н. Толстой", "Ф. М. Достоевский", "М. А. Булгаков",
    "М. А. Шолохов", "А. С. Пушкин", "Н. В. Гоголь",
    "И. С. Тургенев", "М. Ю. Лермонтов", "И. А. Гончаров",
    "И. Ильф, Е. Петров", "Э. М. Ремарк", "Дж. Оруэлл",
    "О. Хаксли",
]


async def clear_tables(session: AsyncSession) -> None:
    """Удаляет все данные из таблиц (для воспроизводимости)."""
    await session.execute(delete(Loan))
    await session.execute(delete(Copy))
    await session.execute(delete(Book))
    await session.execute(delete(Reader))
    await session.commit()


async def seed_small(session: AsyncSession) -> None:
    """Малое наполнение: 50 читателей, 100 книг, 200 экземпляров, 300 выдач."""
    print("Малое наполнение...")
    await _seed(session, n_readers=50, n_books=100, n_copies=200, n_loans=300)


async def seed_working(session: AsyncSession) -> None:
    """Рабочее наполнение: 3000 читателей, 10000 книг, 30000 экземпляров, 50000 выдач."""
    print("Рабочее наполнение...")
    await _seed(
        session,
        n_readers=3000,
        n_books=10000,
        n_copies=30000,
        n_loans=50000,
    )


async def _seed(
    session: AsyncSession,
    n_readers: int,
    n_books: int,
    n_copies: int,
    n_loans: int,
) -> None:
    """Общая логика наполнения."""
    rng = random.Random(SEED)

    # 1. Читатели.
    print(f"  Читатели: {n_readers}...")
    readers = [
        Reader(
            full_name=f"{rng.choice(LAST_NAMES)} {rng.choice(FIRST_NAMES)}",
            card_number=f"CB-{i + 1:06d}",
            email=f"reader{i + 1}@example.com",
            phone=f"+7-9{rng.randint(100000000, 999999999)}",
        )
        for i in range(n_readers)
    ]
    session.add_all(readers)
    await session.commit()

    # 2. Книги.
    print(f"  Книги: {n_books}...")
    books = [
        Book(
            title=f"{rng.choice(BOOK_TITLES)} (том {i + 1})",
            author=rng.choice(BOOK_AUTHORS),
            isbn=f"978-5-{rng.randint(1000000000, 9999999999)}",
            year=rng.randint(1950, 2024),
        )
        for i in range(n_books)
    ]
    session.add_all(books)
    await session.commit()

    # Получаем id-шники после commit.
    book_ids = [b.id for b in books]

    # 3. Экземпляры.
    print(f"  Экземпляры: {n_copies}...")
    copies = [
        Copy(
            book_id=rng.choice(book_ids),
            inventory_number=f"INV-{i + 1:08d}",
            is_available=True,
        )
        for i in range(n_copies)
    ]
    session.add_all(copies)
    await session.commit()

    copy_ids = [c.id for c in copies]
    reader_ids = [r.id for r in readers]

    # 4. Выдачи.
    print(f"  Выдачи: {n_loans}...")
    today = date.today()
    loans: list[Loan] = []
    used_copies: set[int] = set()  # чтобы не выдать один экземпляр дважды одновременно

    for i in range(n_loans):
        # Выбираем экземпляр, который сейчас не занят (для активных выдач).
        # Для возвращённых — можно любой.
        if rng.random() < 0.5:
            # Активная выдача: экземпляр должен быть свободен.
            available = [c for c in copy_ids if c not in used_copies]
            if not available:
                # Если все заняты — делаем возвращённую.
                copy_id = rng.choice(copy_ids)
                returned = True
            else:
                copy_id = rng.choice(available)
                used_copies.add(copy_id)
                returned = False
        else:
            # Возвращённая выдача.
            copy_id = rng.choice(copy_ids)
            returned = True

        # Срок выдачи: случайно в прошлом (от 1 до 365 дней назад).
        issued_at = today - timedelta(days=rng.randint(1, 365))
        due_at = issued_at + timedelta(days=14)

        if returned:
            # Возврат: между issued_at и today.
            days_held = rng.randint(1, 30)
            returned_at = min(issued_at + timedelta(days=days_held), today)
        else:
            returned_at = None

        loans.append(
            Loan(
                reader_id=rng.choice(reader_ids),
                copy_id=copy_id,
                issued_at=issued_at,
                due_at=due_at,
                returned_at=returned_at,
            )
        )

    session.add_all(loans)
    await session.commit()

    # Обновляем is_available у экземпляров, которые остались заняты.
    for c in copies:
        c.is_available = c.id not in used_copies
    await session.commit()


async def main() -> None:
    size = sys.argv[1] if len(sys.argv) > 1 else "small"
    if size not in {"small", "working"}:
        print("Использование: python -m scripts.seed [small|working]")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        await clear_tables(session)
        if size == "small":
            await seed_small(session)
        else:
            await seed_working(session)

    print("Готово.")


if __name__ == "__main__":
    asyncio.run(main())