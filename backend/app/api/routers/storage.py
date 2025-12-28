from fastapi import APIRouter, Depends
from app.services.audit_logger import log_action
from app.db import get_db

router = APIRouter(prefix="/storage", tags=["storage"])


@router.post("/upload-url")
def get_upload_url(filename: str, db=Depends(get_db)):
    # Stubbed; return pretend pre-signed URL
    url = f"https://storage.local/mock/{filename}"
    log_action(db, actor="system", entity_type="storage", entity_id=None, action="generate_upload_url", payload={"filename": filename, "url": url})
    return {"upload_url": url, "provider": "mock-s3"}

