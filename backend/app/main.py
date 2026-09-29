from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.errors import register_error_handlers
from app.logging import configure_logging, get_logger
from app.middleware import RequestLoggingMiddleware
from app.routes import categories, health, tags, tasks, today

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("startup", app=settings.app_name, environment=settings.environment)
    yield
    await engine.dispose()
    log.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)  # added last so it wraps everything
register_error_handlers(app)

API = "/api/v1"
app.include_router(health.router, prefix=API)
app.include_router(tasks.router, prefix=API)
app.include_router(today.router, prefix=API)
app.include_router(categories.router, prefix=API)
app.include_router(tags.router, prefix=API)
