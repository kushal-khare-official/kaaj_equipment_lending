"""
Workflow-related enums and types for the lender matching platform.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ApplicationStep(str, Enum):
    """Steps in the application form that trigger different workflows."""
    BUSINESS_SEARCH = "business_search"      # Step 1: Business lookup
    BUSINESS_DETAILS = "business_details"    # Step 2: Business info confirmed
    GUARANTOR_INFO = "guarantor_info"        # Step 3: Guarantor details entered
    EQUIPMENT_INFO = "equipment_info"        # Step 4: Equipment details entered
    LOAN_DETAILS = "loan_details"            # Step 5: Loan amount/terms entered
    DOCUMENTS = "documents"                  # Step 6: Document upload
    REVIEW = "review"                        # Step 7: Final review
    SUBMITTED = "submitted"                  # Step 8: Application submitted


class CheckType(str, Enum):
    """Types of verification checks that can be run."""
    # Identity & Business Verification
    KYC = "kyc"                              # Know Your Customer - identity verification
    KYB = "kyb"                              # Know Your Business - business verification
    CREDIT_CHECK = "credit_check"            # Personal credit (FICO)
    BUSINESS_CREDIT = "business_credit"      # Business credit (PayNet)

    # Financial Verification
    BANK_VERIFICATION = "bank_verification"  # Bank account verification
    BANK_STATEMENT = "bank_statement"        # Bank statement analysis

    # Additional Checks
    ONLINE_PRESENCE = "online_presence"      # Website, social media verification
    UCC_SEARCH = "ucc_search"                # UCC lien search

    # Document Analysis
    DOCUMENT_ANALYSIS = "document_analysis"  # AI-powered document analysis


class CheckStatus(str, Enum):
    """Status of a verification check."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """Status of a workflow run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some checks completed, some failed


class RiskLevel(str, Enum):
    """Risk level assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(str, Enum):
    """Types of documents that can be requested/analyzed."""
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    DRIVERS_LICENSE = "drivers_license"
    BUSINESS_LICENSE = "business_license"
    PROOF_OF_INSURANCE = "proof_of_insurance"
    EQUIPMENT_INVOICE = "equipment_invoice"
    VOIDED_CHECK = "voided_check"
    ARTICLES_OF_INCORPORATION = "articles_of_incorporation"
    FINANCIAL_STATEMENT = "financial_statement"


# ============================================================================
# Pydantic Models for Workflow Results
# ============================================================================

class CheckResult(BaseModel):
    """Result of a single verification check."""
    check_type: CheckType
    status: CheckStatus
    vendor: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    verified: Optional[bool] = None
    score: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    flags: List[str] = []
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: Optional[int] = None


class WorkflowCheckResults(BaseModel):
    """Container for all check results from a workflow step."""
    step: ApplicationStep
    status: WorkflowStatus
    checks: Dict[str, CheckResult] = {}
    derived_features: Dict[str, Any] = {}
    risk_assessment: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    next_actions: List[str] = []


class DocumentAnalysisResult(BaseModel):
    """Result of AI document analysis."""
    document_type: DocumentType
    status: CheckStatus
    confidence: float = 0.0
    extracted_data: Dict[str, Any] = {}
    validation_flags: List[str] = []
    fraud_indicators: List[str] = []
    summary: Optional[str] = None


# ============================================================================
# Step to Check Mapping - defines which checks run at each step
# ============================================================================

STEP_CHECKS: Dict[ApplicationStep, List[CheckType]] = {
    ApplicationStep.BUSINESS_SEARCH: [],  # No checks, just search

    ApplicationStep.BUSINESS_DETAILS: [
        CheckType.KYB,
        CheckType.BUSINESS_CREDIT,
        CheckType.ONLINE_PRESENCE,
        CheckType.UCC_SEARCH,
    ],

    ApplicationStep.GUARANTOR_INFO: [
        CheckType.KYC,
        CheckType.CREDIT_CHECK,
    ],

    ApplicationStep.EQUIPMENT_INFO: [],  # Feature derivation only

    ApplicationStep.LOAN_DETAILS: [
        CheckType.BANK_VERIFICATION,
    ],

    ApplicationStep.DOCUMENTS: [
        CheckType.DOCUMENT_ANALYSIS,
        CheckType.BANK_STATEMENT,
    ],

    ApplicationStep.REVIEW: [],  # Final matching run

    ApplicationStep.SUBMITTED: [],  # Final state
}


# Checks that should always run when triggered
REQUIRED_CHECKS = {CheckType.KYC, CheckType.KYB, CheckType.CREDIT_CHECK}

# Checks that can be skipped if data is unavailable
OPTIONAL_CHECKS = {CheckType.ONLINE_PRESENCE, CheckType.UCC_SEARCH, CheckType.BANK_STATEMENT}
