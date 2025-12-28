from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_role
from app.models.application import Application, DocumentRequest, DocumentUpload
from app.schemas.documents import (
    DocumentRequestCreate,
    DocumentUploadCreate,
    DocumentRequestOut,
)
from app.shared.enums import Role, DocumentStatus

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/applications/{application_id}/request", response_model=DocumentRequestOut)
def request_document(
    application_id: str,
    payload: DocumentRequestCreate,
    db: Session = Depends(get_db),
    role: Role = Depends(current_role),
):
    if role not in (Role.UNDERWRITER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    dr = DocumentRequest(application_id=application_id, type=payload.type, status=DocumentStatus.REQUESTED)
    db.add(dr)
    db.commit()
    db.refresh(dr)
    return dr


@router.post("/requests/{request_id}/upload", response_model=DocumentRequestOut)
def upload_document(
    request_id: str,
    payload: DocumentUploadCreate,
    db: Session = Depends(get_db),
    role: Role = Depends(current_role),
):
    # merchants can upload; underwriters/admin can also attach
    doc_req = db.query(DocumentRequest).filter(DocumentRequest.id == request_id).first()
    if not doc_req:
        raise HTTPException(status_code=404, detail="Document request not found")
    upload = DocumentUpload(
        request_id=request_id,
        url=payload.url,
        status=payload.status,
        metadata_json=payload.metadata_json,
    )
    doc_req.status = DocumentStatus.UPLOADED
    doc_req.uploads.append(upload)
    db.add(doc_req)
    db.commit()
    db.refresh(doc_req)
    return doc_req

