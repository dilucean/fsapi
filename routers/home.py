from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from lib.utils import tpl, env
from lib.pg import get_pool

r = APIRouter()


@r.get("/", response_class=HTMLResponse)
async def home():
    """
    Home page - renders Jinja2 template.
    """
    template = tpl().get_template("home.html")
    return template.render()


@r.get("/health")
async def health():
    """
    Health check endpoint - returns JSON.
    """
    # Check database connectivity
    pool = get_pool()
    try:
        async with pool.acquire() as conn:
            db_status = await conn.fetchval("SELECT 1")
            db_healthy = db_status == 1
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "app_mode": env("APP_MODE", "production"),
    }
