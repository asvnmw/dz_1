# Library Service

Сервис выдачи книг в библиотеке. Курсовая по оптимизации клиент-серверных приложений.

## Установка

Нужны Python 3.13 и PostgreSQL 16.

```
git clone https://github.com/asvnmw/dz_1.git
cd dz_1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m scripts.init_db
python -m scripts.seed small
uvicorn main:app --reload
```

Перед запуском впиши пароль от PostgreSQL в `.env`.

## Проверка

- http://127.0.0.1:8000
- Логин: demo
- Пароль: demo

## Тесты

```
pytest -v
```

## Операции

| Метод | Путь | Что делает |
|---|---|---|
| POST | /auth/login | Вход |
| POST | /auth/logout | Выход |
| GET | /auth/me | Кто вошёл |
| GET | /api/loans | Список выдач |
| GET | /api/loans/{id} | Одна выдача |
| POST | /api/loans | Выдать книгу |
| POST | /api/loans/{id}/return | Принять возврат |
| GET | /api/readers | Список читателей |
| GET | /api/readers/{id} | Один читатель |
| GET | /api/books | Список книг |
| GET | /api/books/{id} | Одна книга |
| GET | /api/summary | Сводка |