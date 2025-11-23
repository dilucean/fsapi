from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lib.pg import init_pool, close_pool
from lib.utils import env, root
from routers import home

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database connection pool
    await init_pool(
        host=env("DB_HOST", "localhost"),
        port=int(env("DB_PORT", "5432")),
        user=env("DB_USER", "postgres"),
        password=env("DB_PASS", ""),
        database=env("DB_NAME", "postgres"),
    )
    print("Database pool initialized")

    yield

    # Shutdown: Close database connection pool
    await close_pool()
    print("Database pool closed")


app = FastAPI(
    title=env("APP_NAME", "fsapi"),
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = env("CORS_ORIGINS", "").split(",")
if cors_origins and cors_origins[0]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files
app.mount("/static", StaticFiles(directory=str(root() / "static")), name="static")

# Register routers
app.include_router(home.r)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=env("APP_HOST", "0.0.0.0"),
        port=int(env("APP_PORT", "8000")),
        reload=env("APP_MODE") == "dev",
    )
