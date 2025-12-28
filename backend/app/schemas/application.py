from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, model_validator

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
    criterion_results: Optional[List[CriterionResultOut]] = None

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def extract_names_from_criterion_results(cls, data: Any) -> Any:
        """Extract lender_name and program_name from criterion_results if present."""
        if hasattr(data, "__dict__"):
            # It's an ORM model, convert to dict
            cr = getattr(data, "criterion_results", None)
            if isinstance(cr, dict):
                lender_name = cr.get("lender_name")
                program_name = cr.get("program_name")
                criteria = cr.get("criteria", [])
                # Create a new dict with extracted values
                return {
                    "lender_program_id": getattr(data, "lender_program_id", None),
                    "lender_name": lender_name,
                    "program_name": program_name,
                    "eligible": getattr(data, "eligible", False),
                    "fit_score": getattr(data, "fit_score", None),
                    "reasons": getattr(data, "reasons", None),
                    "criterion_results": criteria,
                }
        elif isinstance(data, dict):
            cr = data.get("criterion_results")
            if isinstance(cr, dict):
                data["lender_name"] = cr.get("lender_name")
                data["program_name"] = cr.get("program_name")
                data["criterion_results"] = cr.get("criteria", [])
        return data


class ApplicationOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    merchant_email: str
    document_requests: List[DocumentRequestOut] = []

    class Config:
        from_attributes = True

