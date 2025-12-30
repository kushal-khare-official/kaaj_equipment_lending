from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator


def convert_date_to_str(v: Any) -> Optional[str]:
    """Convert date or datetime to ISO format string."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return v

from app.shared.enums import ApplicationStatus, DocumentStatus


class GuarantorIn(BaseModel):
    is_primary: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    ssn: Optional[str] = None
    dob: Optional[str] = None  # Date of birth (YYYY-MM-DD)
    phone: Optional[str] = None
    email: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
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
    # Business info fields
    business_tin: Optional[str] = None
    business_phone: Optional[str] = None
    business_address_street: Optional[str] = None
    business_address_city: Optional[str] = None
    business_address_state: Optional[str] = None
    business_address_zip: Optional[str] = None
    incorporation_date: Optional[str] = None  # YYYY-MM-DD format


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
    # Business info fields
    business_tin: Optional[str] = None
    business_phone: Optional[str] = None
    business_address_street: Optional[str] = None
    business_address_city: Optional[str] = None
    business_address_state: Optional[str] = None
    business_address_zip: Optional[str] = None
    incorporation_date: Optional[str] = None  # YYYY-MM-DD format


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
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    fico: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator("dob", mode="before")
    @classmethod
    def convert_dob(cls, v: Any) -> Optional[str]:
        return convert_date_to_str(v)


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
    # Business info fields
    business_tin: Optional[str] = None
    business_phone: Optional[str] = None
    business_address_street: Optional[str] = None
    business_address_city: Optional[str] = None
    business_address_state: Optional[str] = None
    business_address_zip: Optional[str] = None
    incorporation_date: Optional[str] = None
    # Review status fields
    review_status: Optional[str] = None
    requires_manual_review: Optional[bool] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    # Assigned lender program
    assigned_lender_program_id: Optional[UUID] = None
    assigned_term_months: Optional[int] = None
    assigned_interest_rate: Optional[float] = None
    # Related entities
    guarantors: List[GuarantorOut] = []
    business_credit: Optional[BusinessCreditOut] = None
    equipment: List[EquipmentOut] = []
    loan_request: Optional[LoanRequestOut] = None
    document_requests: List[DocumentRequestOut] = []

    class Config:
        from_attributes = True

    @field_validator("reviewed_at", "incorporation_date", mode="before")
    @classmethod
    def convert_dates(cls, v: Any) -> Optional[str]:
        """Convert date/datetime to ISO format string during validation."""
        return convert_date_to_str(v)

