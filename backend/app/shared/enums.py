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


class ReviewStatus(str, Enum):
    """Review status for applications after workflow execution."""
    PENDING = "pending"  # Initial state, workflow not yet run
    AUTO_APPROVED = "auto_approved"  # All checks passed, lender matched
    PENDING_MANUAL_REVIEW = "pending_manual_review"  # Document fallback triggered, needs manual review
    MANUALLY_APPROVED = "manually_approved"  # Underwriter approved after manual review
    MANUALLY_REJECTED = "manually_rejected"  # Underwriter rejected after manual review

