from fastapi import FastAPI

from .config import settings
from .api.routers import mock_vendors

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(mock_vendors.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

