from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import register_error_handlers
from app.routes import categories, health, tags, tasks, today


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

API = "/api/v1"
app.include_router(health.router, prefix=API)
app.include_router(tasks.router, prefix=API)
app.include_router(today.router, prefix=API)
app.include_router(categories.router, prefix=API)
app.include_router(tags.router, prefix=API)
