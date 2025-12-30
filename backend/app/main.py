import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.routers import mock_vendors, applications, lenders, match, documents, audit, storage, workflow

logger = logging.getLogger(__name__)

# Global reference to worker task
_worker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start/stop Hatchet worker."""
    global _worker_task
    
    # Startup: Start Hatchet worker if configured
    if settings.hatchet_client_token:
        try:
            from .workflows.worker import create_worker
            worker = create_worker()
            _worker_task = asyncio.create_task(worker.async_start())
            logger.info("Hatchet worker started successfully")
        except Exception as e:
            logger.warning(f"Failed to start Hatchet worker: {e}")
            logger.info("Application will continue without workflow support")
    else:
        logger.info("Hatchet not configured - skipping worker startup")
    
    yield  # Application runs here
    
    # Shutdown: Stop worker if running
    if _worker_task:
        logger.info("Stopping Hatchet worker...")
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        logger.info("Hatchet worker stopped")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

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
    return {"status": "ok", "hatchet_worker": _worker_task is not None and not _worker_task.done()}

