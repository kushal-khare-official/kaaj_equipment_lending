from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.shared.enums import DocumentStatus


class DocumentRequestCreate(BaseModel):
    type: str


class DocumentUploadCreate(BaseModel):
    url: str
    status: Optional[str] = None
    metadata_json: Optional[dict] = None


class DocumentUploadOut(BaseModel):
    id: UUID
    url: str
    status: Optional[str]
    metadata_json: Optional[dict] = None

    class Config:
        from_attributes = True


class DocumentRequestOut(BaseModel):
    id: UUID
    type: str
    status: DocumentStatus
    uploads: list[DocumentUploadOut] = []
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

