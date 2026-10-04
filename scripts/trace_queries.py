"""Разложение времени операций на БД и код приложения.

Не использует pg_stat_statements_reset (нужны права суперпользователя).
Вместо этого снимает «снимок» статистики до и после серии и вычитает.

Запуск (сервер должен быть уже запущен):
    python -m scripts.trace_queries
"""
import asyncio
import statistics
import time

import httpx
from sqlalchemy import text

from app.database import AsyncSessionLocal

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "demo"
PASSWORD = "demo"

WARMUP = 2
REPEATS = 20

OPERATIONS = [
    ("GET  /api/summary", "GET", "/api/summary"),
    ("GET  /api/loans?only_active=true", "GET", "/api/loans?only_active=true"),
]


async def login(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    resp.raise_for_status()


async def snapshot_pg() -> tuple[float, int]:
    """Снимок: (суммарное время, суммарное число вызовов) по всем запросам."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT COALESCE(SUM(total_exec_time), 0) AS t, "
                "COALESCE(SUM(calls), 0) AS c "
                "FROM pg_stat_statements"
            )
        )
        row = result.one()
        return float(row[0]), int(row[1])


async def measure_operation(
    client: httpx.AsyncClient,
    method: str,
    path: str,
) -> dict:
    # Прогрев — не считаем.
    for _ in range(WARMUP):
        await client.request(method, f"{BASE_URL}{path}")

    # Снимок до серии.
    t_before, c_before = await snapshot_pg()

    # Измерительная серия.
    times: list[float] = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        resp = await client.request(method, f"{BASE_URL}{path}")
        elapsed_ms = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        times.append(elapsed_ms)

    # Снимок после серии.
    t_after, c_after = await snapshot_pg()

    # Разница — то, что накопилось за серию.
    db_ms_total = t_after - t_before
    db_calls_total = c_after - c_before

    db_ms = db_ms_total / REPEATS
    db_calls = db_calls_total / REPEATS
    p50 = statistics.median(times)

    return {
        "p50_total_ms": p50,
        "db_ms": db_ms,
        "code_ms": p50 - db_ms,
        "db_calls": db_calls,
    }


async def main() -> None:
    async with httpx.AsyncClient(timeout=60.0) as client:
        await login(client)

        print(f"Разложение времени: прогрев {WARMUP}, повторов {REPEATS}, учётка {USERNAME}")
        print()

        header = (
            f"{'Операция':<35} "
            f"{'Время, мс':>11} "
            f"{'В БД, мс':>11} "
            f"{'В коде, мс':>12} "
            f"{'Запросов':>10}"
        )
        print(header)
        print("-" * len(header))

        for name, method, path in OPERATIONS:
            try:
                r = await measure_operation(client, method, path)
                print(
                    f"{name:<35} "
                    f"{r['p50_total_ms']:>11.2f} "
                    f"{r['db_ms']:>11.2f} "
                    f"{r['code_ms']:>12.2f} "
                    f"{r['db_calls']:>10.1f}"
                )
            except Exception as e:
                print(f"{name:<35} ОШИБКА: {e}")


if __name__ == "__main__":
    asyncio.run(main())