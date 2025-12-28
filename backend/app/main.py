from fastapi import FastAPI

from .config import settings
from .api.routers import mock_vendors, applications, lenders, match, documents, audit

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(mock_vendors.router)
app.include_router(applications.router)
app.include_router(lenders.router)
app.include_router(match.router)
app.include_router(documents.router)
app.include_router(audit.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

