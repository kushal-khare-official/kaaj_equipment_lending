from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.shared.enums import ApplicationStatus, DocumentStatus


class GuarantorIn(BaseModel):
    is_primary: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    ssn: Optional[str] = None
    fico: Optional[int] = None
    cdl_flag: bool = False
    homeownership: Optional[bool] = None


class BusinessCreditIn(BaseModel):
    paynet_score: Optional[int] = None
    revolving_utilization: Optional[int] = None


class EquipmentIn(BaseModel):
    type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
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
    guarantors: List[GuarantorIn] = []
    business_credit: Optional[BusinessCreditIn] = None
    equipment: List[EquipmentIn] = []
    loan_request: Optional[LoanRequestIn] = None
    # Optional fields for intake form prefill
    business_name: Optional[str] = None
    loan_type: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Schema for updating an application - all fields optional."""
    merchant_email: Optional[str] = None
    business_name: Optional[str] = None
    loan_type: Optional[str] = None
    guarantors: Optional[List[GuarantorIn]] = None
    business_credit: Optional[BusinessCreditIn] = None
    equipment: Optional[List[EquipmentIn]] = None
    loan_request: Optional[LoanRequestIn] = None
    current_step: Optional[int] = None  # Track which step the user is on


class DocumentRequestOut(BaseModel):
    id: UUID
    type: str
    status: DocumentStatus

    class Config:
        from_attributes = True


class CriterionResultOut(BaseModel):
    field: str
    operator: str
    data_type: str
    value: Optional[str] = None
    expected: Optional[str] = None
    passed: bool
    description: Optional[str] = None


class MatchResultOut(BaseModel):
    lender_program_id: Optional[UUID] = None
    lender_name: Optional[str] = None
    program_name: Optional[str] = None
    eligible: bool
    fit_score: Optional[int] = None
    reasons: Optional[str] = None
    assigned_term_months: Optional[int] = None
    assigned_interest_rate: Optional[float] = None
    criterion_results: Optional[List[CriterionResultOut]] = None

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def extract_names_from_criterion_results(cls, data: Any) -> Any:
        """Extract lender_name, program_name, assigned_term_months, and assigned_interest_rate from criterion_results if present."""
        if hasattr(data, "__dict__"):
            # It's an ORM model, convert to dict
            cr = getattr(data, "criterion_results", None)
            if isinstance(cr, dict):
                lender_name = cr.get("lender_name")
                program_name = cr.get("program_name")
                assigned_term_months = cr.get("assigned_term_months")
                assigned_interest_rate = cr.get("assigned_interest_rate")
                criteria = cr.get("criteria", [])
                # Create a new dict with extracted values
                return {
                    "lender_program_id": getattr(data, "lender_program_id", None),
                    "lender_name": lender_name,
                    "program_name": program_name,
                    "eligible": getattr(data, "eligible", False),
                    "fit_score": getattr(data, "fit_score", None),
                    "reasons": getattr(data, "reasons", None),
                    "assigned_term_months": assigned_term_months,
                    "assigned_interest_rate": assigned_interest_rate,
                    "criterion_results": criteria,
                }
        elif isinstance(data, dict):
            cr = data.get("criterion_results")
            if isinstance(cr, dict):
                data["lender_name"] = cr.get("lender_name")
                data["program_name"] = cr.get("program_name")
                data["assigned_term_months"] = cr.get("assigned_term_months")
                data["assigned_interest_rate"] = cr.get("assigned_interest_rate")
                data["criterion_results"] = cr.get("criteria", [])
        return data


class GuarantorOut(BaseModel):
    id: UUID
    is_primary: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    ssn: Optional[str] = None
    fico: Optional[int] = None

    class Config:
        from_attributes = True


class BusinessCreditOut(BaseModel):
    paynet_score: Optional[int] = None
    revolving_utilization: Optional[int] = None

    class Config:
        from_attributes = True


class EquipmentOut(BaseModel):
    id: UUID
    type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    titled: bool = False
    private_party: bool = False

    class Config:
        from_attributes = True


class LoanRequestOut(BaseModel):
    amount: Optional[float] = None
    term_months: Optional[int] = None
    down_payment: Optional[float] = None

    class Config:
        from_attributes = True


class ApplicationOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    merchant_email: str
    business_name: Optional[str] = None
    loan_type: Optional[str] = None
    created_at: Optional[str] = None
    document_requests: List[DocumentRequestOut] = []

    class Config:
        from_attributes = True


class ApplicationListOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    merchant_email: str
    business_name: Optional[str] = None
    loan_type: Optional[str] = None
    loan_amount: Optional[float] = None
    created_at: Optional[str] = None
    criteria_met: Optional[str] = None
    fit_score: Optional[int] = None

    class Config:
        from_attributes = True


class ApplicationDetailOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    merchant_email: str
    business_name: Optional[str] = None
    loan_type: Optional[str] = None
    current_step: Optional[int] = None
    guarantors: List[GuarantorOut] = []
    business_credit: Optional[BusinessCreditOut] = None
    equipment: List[EquipmentOut] = []
    loan_request: Optional[LoanRequestOut] = None
    document_requests: List[DocumentRequestOut] = []

    class Config:
        from_attributes = True

