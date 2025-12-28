from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.deps import current_role
from app.models.application import Application, DocumentRequest, DocumentUpload
from app.schemas.documents import (
    DocumentRequestCreate,
    DocumentUploadCreate,
    DocumentRequestOut,
)
from app.shared.enums import Role, DocumentStatus
from app.services.audit_logger import log_action
from app.schemas.documents import DocumentRequestOut

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
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application_id")
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    dr = DocumentRequest(application_id=application_id, type=payload.type, status=DocumentStatus.REQUESTED)
    db.add(dr)
    db.commit()
    db.refresh(dr)
    log_action(db, actor="underwriter", entity_type="document_request", entity_id=dr.id, action="request_document", application_id=app.id, payload=payload.model_dump())
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
    log_action(db, actor="merchant", entity_type="document_upload", entity_id=upload.id, action="upload_document", application_id=doc_req.application_id, payload=payload.model_dump())
    return doc_req


@router.get("/applications/{application_id}", response_model=list[DocumentRequestOut])
def list_documents(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application_id")
    return (
        db.query(DocumentRequest)
        .filter(DocumentRequest.application_id == app_id)
        .order_by(DocumentRequest.created_at.desc())
        .all()
    )

