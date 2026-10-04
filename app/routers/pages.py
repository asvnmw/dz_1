"""HTML-страницы для ручной проверки сценариев."""
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    session_id: Annotated[str | None, Cookie()] = None,
):
    from app.auth import _sessions
    if session_id is None or session_id not in _sessions:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "loans_list.html")


@router.get("/loans", response_class=HTMLResponse)
async def loans_page(
    request: Request,
    session_id: Annotated[str | None, Cookie()] = None,
):
    from app.auth import _sessions
    if session_id is None or session_id not in _sessions:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "loans_list.html")


@router.get("/loans/{loan_id}", response_class=HTMLResponse)
async def loan_detail_page(
    request: Request,
    loan_id: int,
    session_id: Annotated[str | None, Cookie()] = None,
):
    from app.auth import _sessions
    if session_id is None or session_id not in _sessions:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "loan_detail.html",
        {"loan_id": loan_id},
    )


@router.get("/summary", response_class=HTMLResponse)
async def summary_page(
    request: Request,
    session_id: Annotated[str | None, Cookie()] = None,
):
    from app.auth import _sessions
    if session_id is None or session_id not in _sessions:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "summary.html")