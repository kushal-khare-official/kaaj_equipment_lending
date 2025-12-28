from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.shared.enums import ApplicationStatus, DocumentStatus


class GuarantorIn(BaseModel):
    is_primary: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    fico: Optional[int] = None
    cdl_flag: bool = False
    homeownership: Optional[bool] = None


class BusinessCreditIn(BaseModel):
    paynet_score: Optional[int] = None
    revolving_utilization: Optional[int] = None


class EquipmentIn(BaseModel):
    type: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    titled: bool = False
    private_party: bool = False
    hours: Optional[int] = None


class LoanRequestIn(BaseModel):
    amount: Optional[float] = None
    term_months: Optional[int] = None
    down_payment: Optional[float] = None


class ApplicationCreate(BaseModel):
    merchant_email: str
    guarantors: List[GuarantorIn]
    business_credit: Optional[BusinessCreditIn] = None
    equipment: List[EquipmentIn] = []
    loan_request: Optional[LoanRequestIn] = None


class DocumentRequestOut(BaseModel):
    id: UUID
    type: str
    status: DocumentStatus

    class Config:
        from_attributes = True


class MatchResultOut(BaseModel):
    lender_program_id: UUID
    eligible: bool
    fit_score: Optional[int]
    reasons: Optional[str]
    criterion_results: Optional[dict]

    class Config:
        from_attributes = True


class ApplicationOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    merchant_email: str
    document_requests: List[DocumentRequestOut] = []

    class Config:
        from_attributes = True

