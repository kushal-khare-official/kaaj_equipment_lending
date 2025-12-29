from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.routers import mock_vendors, applications, lenders, match, documents, audit, storage, workflow

app = FastAPI(title=settings.app_name, version="0.1.0")

# Allow local dev origins; adjust as needed for deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_vendors.router)
app.include_router(applications.router)
app.include_router(lenders.router)
app.include_router(match.router)
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(storage.router)
app.include_router(workflow.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

