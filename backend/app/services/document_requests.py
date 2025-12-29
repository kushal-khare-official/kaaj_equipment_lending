"""
Document Request Service for intelligent document requests based on failed checks.

This service provides:
1. Industry-standard document requirements mapped to check types
2. Automatic document request creation when checks fail
3. Risk-based document escalation
"""
import logging
from typing import List, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.application import Application, DocumentRequest
from app.services.audit_logger import log_action
from app.shared.enums import DocumentStatus
from app.shared.workflow_enums import (
    CheckType,
    CheckStatus,
    RiskLevel,
    CheckResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Industry-Standard Document Requirements by Check Type
# =============================================================================

# Documents to request when a specific check fails
CHECK_FAILURE_DOCUMENTS: Dict[CheckType, List[str]] = {
    # KYC failures - identity verification documents
    CheckType.KYC: [
        "drivers_license",
        "passport",
        "utility_bill",  # For address verification
    ],

    # KYB failures - business verification documents
    CheckType.KYB: [
        "articles_of_incorporation",
        "business_license",
        "certificate_of_good_standing",
        "ein_letter",  # IRS EIN confirmation letter
    ],

    # Credit check failures - financial health documents
    CheckType.CREDIT_CHECK: [
        "bank_statements_3_months",
        "tax_returns_2_years",
        "personal_financial_statement",
    ],

    # Business credit failures - business financial documents
    CheckType.BUSINESS_CREDIT: [
        "bank_statements_6_months",
        "profit_loss_statement",
        "balance_sheet",
        "aged_receivables",
    ],

    # Bank verification failures
    CheckType.BANK_VERIFICATION: [
        "voided_check",
        "bank_statements_3_months",
        "bank_letter",  # Bank verification letter
    ],

    # Bank statement analysis flags
    CheckType.BANK_STATEMENT: [
        "bank_statements_6_months",
        "explanation_letter",  # For unusual transactions
        "deposit_verification",  # For large deposits
    ],

    # Online presence issues
    CheckType.ONLINE_PRESENCE: [
        "business_license",
        "utility_bill_business",
        "lease_agreement",
    ],

    # UCC search issues
    CheckType.UCC_SEARCH: [
        "ucc_releases",
        "payoff_letters",
        "lien_subordination",
    ],

    # Document analysis failures
    CheckType.DOCUMENT_ANALYSIS: [
        "original_documents",
        "notarized_copies",
    ],
}

# Additional documents based on risk level
RISK_ESCALATION_DOCUMENTS: Dict[RiskLevel, List[str]] = {
    RiskLevel.LOW: [],

    RiskLevel.MEDIUM: [
        "additional_id",  # Secondary form of ID
    ],

    RiskLevel.HIGH: [
        "personal_guarantee",
        "collateral_documentation",
        "references_business",
    ],

    RiskLevel.CRITICAL: [
        "personal_guarantee",
        "collateral_documentation",
        "references_business",
        "explanation_letter",
        "additional_collateral",
    ],
}

# Documents based on specific risk flags
FLAG_DOCUMENTS: Dict[str, List[str]] = {
    "low_fico_score": ["personal_financial_statement", "explanation_letter"],
    "low_paynet_score": ["bank_statements_6_months", "aged_receivables"],
    "high_credit_utilization": ["debt_schedule", "payoff_plan"],
    "startup_business": ["business_plan", "personal_tax_returns"],
    "identity_not_verified": ["drivers_license", "passport", "ssn_card"],
    "address_not_verified": ["utility_bill", "lease_agreement"],
    "business_not_verified": ["articles_of_incorporation", "ein_letter"],
    "watchlist_hit": ["explanation_letter", "compliance_documentation"],
    "nsf_count_": ["bank_statements_6_months", "explanation_letter"],
    "overdraft_count_": ["bank_statements_6_months", "explanation_letter"],
    "low_bank_balance": ["bank_statements_6_months", "accounts_receivable"],
    "name_mismatch": ["legal_name_documentation", "dba_certificate"],
    "possible_tampering": ["original_documents", "notarized_copies"],
    "existing_liens_": ["ucc_releases", "payoff_letters"],
    "multiple_liens_": ["ucc_releases", "payoff_letters", "lien_subordination"],
    "weak_online_presence": ["business_license", "utility_bill_business"],
    "new_domain": ["business_license", "years_in_business_proof"],
    "high_fraud_score": ["additional_id", "notarized_documents"],
    "large_deposits_": ["deposit_verification", "source_of_funds"],
    "delinquencies_": ["explanation_letter", "payment_history"],
}


class DocumentRequestService:
    """
    Service for creating intelligent document requests based on check results.
    """

    def get_required_documents(
        self,
        check_results: Dict[str, CheckResult],
        overall_risk: Optional[RiskLevel] = None,
    ) -> List[str]:
        """
        Determine which documents to request based on check results.

        Args:
            check_results: Dict of check type to CheckResult
            overall_risk: Overall risk level from workflow

        Returns:
            List of unique document types to request
        """
        documents = set()

        for check_type_str, result in check_results.items():
            if not isinstance(result, CheckResult):
                continue

            # Add documents for failed or needs_review checks
            if result.status in [CheckStatus.FAILED, CheckStatus.NEEDS_REVIEW]:
                check_docs = CHECK_FAILURE_DOCUMENTS.get(result.check_type, [])
                documents.update(check_docs)

            # Add documents based on risk flags
            for flag in result.flags:
                # Handle flags with numeric suffixes (e.g., "nsf_count_3")
                base_flag = flag
                for key in FLAG_DOCUMENTS:
                    if flag.startswith(key.rstrip("_")):
                        base_flag = key
                        break

                flag_docs = FLAG_DOCUMENTS.get(base_flag, [])
                documents.update(flag_docs)

        # Add documents based on overall risk level
        if overall_risk:
            risk_docs = RISK_ESCALATION_DOCUMENTS.get(overall_risk, [])
            documents.update(risk_docs)

        return list(documents)

    def create_document_requests(
        self,
        db: Session,
        application: Application,
        document_types: List[str],
        requested_by: str = "system",
    ) -> List[DocumentRequest]:
        """
        Create document request records for the specified document types.

        Avoids creating duplicates for already-requested documents.

        Args:
            db: Database session
            application: Application to request documents for
            document_types: List of document types to request
            requested_by: Actor requesting the documents

        Returns:
            List of created DocumentRequest objects
        """
        # Get existing document requests
        existing_types = {
            doc.type for doc in application.document_requests
        }

        created = []
        for doc_type in document_types:
            if doc_type not in existing_types:
                doc_request = DocumentRequest(
                    application_id=application.id,
                    type=doc_type,
                    status=DocumentStatus.REQUESTED,
                    requested_by=requested_by,
                )
                db.add(doc_request)
                created.append(doc_request)

        if created:
            db.commit()
            for doc in created:
                db.refresh(doc)

            # Log the action
            log_action(
                db,
                actor=requested_by,
                entity_type="document_request",
                entity_id=None,
                action="auto_document_request",
                application_id=application.id,
                payload={
                    "document_types": [d.type for d in created],
                    "total_requested": len(created),
                },
            )

            logger.info(
                f"Created {len(created)} document requests for application {application.id}"
            )

        return created

    def process_check_results(
        self,
        db: Session,
        application: Application,
        check_results: Dict[str, CheckResult],
        overall_risk: Optional[RiskLevel] = None,
    ) -> List[DocumentRequest]:
        """
        Process check results and create appropriate document requests.

        This is the main entry point for the document request workflow.

        Args:
            db: Database session
            application: Application being processed
            check_results: Results from verification checks
            overall_risk: Overall risk assessment

        Returns:
            List of created document requests
        """
        # Get required documents
        required_docs = self.get_required_documents(check_results, overall_risk)

        if not required_docs:
            logger.info(f"No documents required for application {application.id}")
            return []

        # Create document requests
        return self.create_document_requests(
            db,
            application,
            required_docs,
            requested_by="workflow",
        )


# =============================================================================
# Document Type Metadata
# =============================================================================

DOCUMENT_TYPE_METADATA: Dict[str, Dict[str, str]] = {
    "drivers_license": {
        "display_name": "Driver's License",
        "description": "Valid government-issued driver's license",
        "category": "identity",
    },
    "passport": {
        "display_name": "Passport",
        "description": "Valid passport (any country)",
        "category": "identity",
    },
    "ssn_card": {
        "display_name": "Social Security Card",
        "description": "Social Security card or letter",
        "category": "identity",
    },
    "utility_bill": {
        "display_name": "Utility Bill",
        "description": "Recent utility bill for address verification (within 60 days)",
        "category": "address",
    },
    "articles_of_incorporation": {
        "display_name": "Articles of Incorporation",
        "description": "State-filed articles of incorporation or organization",
        "category": "business",
    },
    "business_license": {
        "display_name": "Business License",
        "description": "Current business license or permit",
        "category": "business",
    },
    "certificate_of_good_standing": {
        "display_name": "Certificate of Good Standing",
        "description": "State-issued certificate of good standing",
        "category": "business",
    },
    "ein_letter": {
        "display_name": "EIN Confirmation Letter",
        "description": "IRS EIN/TIN confirmation letter (Form CP 575)",
        "category": "business",
    },
    "bank_statements_3_months": {
        "display_name": "Bank Statements (3 Months)",
        "description": "Last 3 months of complete business bank statements",
        "category": "financial",
    },
    "bank_statements_6_months": {
        "display_name": "Bank Statements (6 Months)",
        "description": "Last 6 months of complete business bank statements",
        "category": "financial",
    },
    "tax_returns_2_years": {
        "display_name": "Tax Returns (2 Years)",
        "description": "Complete business and/or personal tax returns for last 2 years",
        "category": "financial",
    },
    "personal_tax_returns": {
        "display_name": "Personal Tax Returns",
        "description": "Personal tax returns for all guarantors",
        "category": "financial",
    },
    "personal_financial_statement": {
        "display_name": "Personal Financial Statement",
        "description": "Current personal financial statement for guarantors",
        "category": "financial",
    },
    "profit_loss_statement": {
        "display_name": "Profit & Loss Statement",
        "description": "Year-to-date profit and loss statement",
        "category": "financial",
    },
    "balance_sheet": {
        "display_name": "Balance Sheet",
        "description": "Current balance sheet",
        "category": "financial",
    },
    "aged_receivables": {
        "display_name": "Aged Receivables",
        "description": "Aged accounts receivable report",
        "category": "financial",
    },
    "voided_check": {
        "display_name": "Voided Check",
        "description": "Voided check for bank account verification",
        "category": "banking",
    },
    "bank_letter": {
        "display_name": "Bank Verification Letter",
        "description": "Letter from bank verifying account ownership",
        "category": "banking",
    },
    "business_plan": {
        "display_name": "Business Plan",
        "description": "Detailed business plan (for startups)",
        "category": "business",
    },
    "equipment_invoice": {
        "display_name": "Equipment Invoice",
        "description": "Invoice or bill of sale for equipment",
        "category": "equipment",
    },
    "personal_guarantee": {
        "display_name": "Personal Guarantee",
        "description": "Signed personal guarantee agreement",
        "category": "collateral",
    },
    "collateral_documentation": {
        "display_name": "Collateral Documentation",
        "description": "Documentation of additional collateral",
        "category": "collateral",
    },
    "ucc_releases": {
        "display_name": "UCC Releases",
        "description": "UCC lien release documentation",
        "category": "liens",
    },
    "payoff_letters": {
        "display_name": "Payoff Letters",
        "description": "Payoff letters for existing loans",
        "category": "liens",
    },
    "lien_subordination": {
        "display_name": "Lien Subordination Agreement",
        "description": "Subordination agreement for existing liens",
        "category": "liens",
    },
    "explanation_letter": {
        "display_name": "Explanation Letter",
        "description": "Written explanation for flagged items",
        "category": "supporting",
    },
    "additional_id": {
        "display_name": "Additional ID",
        "description": "Secondary form of government-issued ID",
        "category": "identity",
    },
    "references_business": {
        "display_name": "Business References",
        "description": "Trade or business references",
        "category": "supporting",
    },
    "debt_schedule": {
        "display_name": "Debt Schedule",
        "description": "Complete schedule of all existing debts",
        "category": "financial",
    },
    "deposit_verification": {
        "display_name": "Deposit Verification",
        "description": "Source documentation for large deposits",
        "category": "banking",
    },
    "source_of_funds": {
        "display_name": "Source of Funds",
        "description": "Documentation showing source of funds",
        "category": "banking",
    },
    "original_documents": {
        "display_name": "Original Documents",
        "description": "Original versions of flagged documents",
        "category": "supporting",
    },
    "notarized_copies": {
        "display_name": "Notarized Copies",
        "description": "Notarized copies of required documents",
        "category": "supporting",
    },
    "lease_agreement": {
        "display_name": "Lease Agreement",
        "description": "Current business lease agreement",
        "category": "business",
    },
    "utility_bill_business": {
        "display_name": "Business Utility Bill",
        "description": "Utility bill in business name",
        "category": "business",
    },
    "dba_certificate": {
        "display_name": "DBA Certificate",
        "description": "Doing Business As certificate",
        "category": "business",
    },
    "legal_name_documentation": {
        "display_name": "Legal Name Documentation",
        "description": "Legal name change documentation",
        "category": "identity",
    },
    "proof_of_insurance": {
        "display_name": "Proof of Insurance",
        "description": "Current business insurance certificate",
        "category": "business",
    },
}


def get_document_metadata(doc_type: str) -> Dict[str, str]:
    """Get metadata for a document type."""
    return DOCUMENT_TYPE_METADATA.get(doc_type, {
        "display_name": doc_type.replace("_", " ").title(),
        "description": f"Please provide: {doc_type.replace('_', ' ')}",
        "category": "other",
    })


# Singleton instance
document_request_service = DocumentRequestService()
