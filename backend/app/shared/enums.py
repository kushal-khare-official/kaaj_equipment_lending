from enum import Enum


class ApplicationStatus(str, Enum):
    PROCESSING = "processing"
    PENDING_DOCS = "pending_docs"
    APPROVED = "approved"
    DECLINED = "declined"
    COMPLETED = "completed"
    CLOSED = "closed"


class Role(str, Enum):
    MERCHANT = "merchant"
    UNDERWRITER = "underwriter"
    ADMIN = "admin"


class DocumentStatus(str, Enum):
    REQUESTED = "requested"
    UPLOADED = "uploaded"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"

