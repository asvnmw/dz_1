"""Замер времени ответа операций API.

Методика (методичка, стр. 10):
- прогрев перед серией (результаты в расчёт не идут);
- не менее 20 повторов;
- одна учётная запись (demo/demo);
- считаем p50 (медиану), p95, max.

Запуск (сервер должен быть уже запущен):
    python -m scripts.benchmark
"""
import asyncio
import statistics
import time

import httpx

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "demo"
PASSWORD = "demo"

# Сколько прогревочных запросов (в расчёт не идут) и сколько измерительных.
WARMUP = 2
REPEATS = 20


async def login(client: httpx.AsyncClient) -> None:
    """Логин, чтобы получить куку сессии."""
    resp = await client.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    resp.raise_for_status()


async def measure(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    body: dict | None,
) -> dict:
    """Один замер одной операции — с прогревом и серией повторов."""
    # Прогрев — не считаем.
    for _ in range(WARMUP):
        if method == "GET":
            await client.get(f"{BASE_URL}{path}")
        else:
            await client.post(f"{BASE_URL}{path}", json=body)

    # Измерительная серия.
    times: list[float] = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        if method == "GET":
            resp = await client.get(f"{BASE_URL}{path}")
        else:
            resp = await client.post(f"{BASE_URL}{path}", json=body)
        elapsed_ms = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        times.append(elapsed_ms)

    times.sort()
    return {
        "p50": statistics.median(times),
        "p95": times[int(len(times) * 0.95) - 1] if len(times) >= 2 else times[0],
        "max": max(times),
    }


async def main() -> None:
    async with httpx.AsyncClient(timeout=60.0) as client:
        await login(client)

        # Узнаём реальные id первой выдачи и первой книги.
        loans_resp = await client.get(f"{BASE_URL}/api/loans?page=1&size=1")
        loans_resp.raise_for_status()
        loans = loans_resp.json()["items"]
        if not loans:
            print("В БД нет выдач — нечего измерять. Запусти seed.")
            return
        real_loan_id = loans[0]["id"]

        books_resp = await client.get(f"{BASE_URL}/api/books?page=1&size=1")
        books_resp.raise_for_status()
        books = books_resp.json()["items"]
        real_book_id = books[0]["id"] if books else None

        # Собираем операции с реальными id.
        operations: list[tuple[str, str, str, dict | None]] = [
            ("GET  /api/loans", "GET", "/api/loans?page=1&size=20", None),
            ("GET  /api/loans?only_active=true", "GET", "/api/loans?only_active=true", None),
            (f"GET  /api/loans/{real_loan_id}", "GET", f"/api/loans/{real_loan_id}", None),
            ("GET  /api/summary", "GET", "/api/summary", None),
            ("GET  /api/readers", "GET", "/api/readers?page=1&size=20", None),
            ("GET  /api/books", "GET", "/api/books?page=1&size=20", None),
        ]
        if real_book_id is not None:
            operations.append(
                (f"GET  /api/books/{real_book_id}", "GET", f"/api/books/{real_book_id}", None),
            )

        print(f"Замеры: прогрев {WARMUP}, повторов {REPEATS}, учётка {USERNAME}")
        print()
        print(f"{'Операция':<40} {'p50, мс':>10} {'p95, мс':>10} {'max, мс':>10}")
        print("-" * 72)

        for name, method, path, body in operations:
            try:
                result = await measure(client, method, path, body)
                print(
                    f"{name:<40} "
                    f"{result['p50']:>10.2f} "
                    f"{result['p95']:>10.2f} "
                    f"{result['max']:>10.2f}"
                )
            except Exception as e:
                print(f"{name:<40} ОШИБКА: {e}")


if __name__ == "__main__":
    asyncio.run(main())