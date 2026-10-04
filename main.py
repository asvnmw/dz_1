from fastapi import FastAPI

from app.routers import auth as auth_router
from app.routers import books as books_router
from app.routers import loans as loans_router
from app.routers import pages as pages_router
from app.routers import readers as readers_router
from app.routers import summary as summary_router

app = FastAPI(
    title="Library Service",
    description="Учебный сервис выдачи книг. Курсовая по дисциплине "
                "«Оптимизация клиент-серверных приложений».",
    version="0.1.0",
)

app.include_router(pages_router.router)
app.include_router(auth_router.router)
app.include_router(loans_router.router)
app.include_router(readers_router.router)
app.include_router(books_router.router)
app.include_router(summary_router.router)