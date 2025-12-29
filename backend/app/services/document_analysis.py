"""
Document Analysis Service for AI-powered document verification.

This service handles:
1. Document type classification
2. Data extraction from documents
3. Fraud detection
4. Validation against application data
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List

import httpx

from app.shared.workflow_enums import (
    CheckType,
    CheckStatus,
    CheckResult,
    RiskLevel,
    DocumentType,
    DocumentAnalysisResult,
)

logger = logging.getLogger(__name__)

VENDOR_BASE_URL = "http://localhost:8000/mock"
DEFAULT_TIMEOUT = 60.0  # Document analysis may take longer
MAX_RETRIES = 2


class DocumentAnalysisService:
    """
    AI-powered document analysis service.

    Capabilities:
    - Document classification (identify document type)
    - OCR and data extraction
    - Fraud detection (tampering, forgery)
    - Consistency validation
    - Bank statement analysis
    """

    def __init__(self, base_url: str = VENDOR_BASE_URL):
        self.base_url = base_url

    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """Make an HTTP request to document analysis endpoint."""
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=payload,
                    )
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                logger.warning(f"Document analysis request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
        raise Exception(f"Document analysis failed after {MAX_RETRIES} attempts")

    # =========================================================================
    # Document Classification
    # =========================================================================
    async def classify_document(
        self,
        document_url: str,
    ) -> DocumentAnalysisResult:
        """
        Classify a document to determine its type.

        Uses AI vision to identify:
        - Bank statements
        - Tax returns
        - Driver's licenses
        - Business documents
        - Equipment invoices
        """
        start_time = time.time()

        try:
            response = await self._make_request(
                "/document-classify",
                {"document_url": document_url},
            )

            doc_type_str = response.get("document_type", "unknown")
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.FINANCIAL_STATEMENT

            return DocumentAnalysisResult(
                document_type=doc_type,
                status=CheckStatus.COMPLETED,
                confidence=response.get("confidence", 0.0),
                extracted_data=response.get("extracted_data", {}),
                validation_flags=response.get("validation_flags", []),
                fraud_indicators=response.get("fraud_indicators", []),
                summary=response.get("summary"),
            )

        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            return DocumentAnalysisResult(
                document_type=DocumentType.FINANCIAL_STATEMENT,
                status=CheckStatus.FAILED,
                confidence=0.0,
            )

    # =========================================================================
    # Bank Statement Analysis
    # =========================================================================
    async def analyze_bank_statement(
        self,
        document_url: str,
        expected_business_name: Optional[str] = None,
        expected_account_holder: Optional[str] = None,
    ) -> CheckResult:
        """
        Analyze bank statements for underwriting.

        Extracts and validates:
        - Account holder name
        - Average daily balance
        - Monthly deposits/withdrawals
        - NSF/overdraft history
        - Large deposits (potential fraud indicator)
        - Consistency with application data
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.BANK_STATEMENT,
            status=CheckStatus.RUNNING,
            vendor="document-ai",
        )

        try:
            response = await self._make_request(
                "/bank-statement-analysis",
                {
                    "document_url": document_url,
                    "expected_business_name": expected_business_name,
                    "expected_account_holder": expected_account_holder,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("verified", False)

            details = response.get("details", {})

            # Extract key metrics
            avg_balance = details.get("average_daily_balance", 0)
            monthly_deposits = details.get("monthly_deposits", 0)
            nsf_count = details.get("nsf_count", 0)
            overdraft_count = details.get("overdraft_count", 0)

            result.score = int(avg_balance)

            # Assess risk
            if avg_balance >= 25000 and nsf_count == 0:
                result.risk_level = RiskLevel.LOW
            elif avg_balance >= 10000 and nsf_count <= 1:
                result.risk_level = RiskLevel.MEDIUM
            elif avg_balance >= 5000:
                result.risk_level = RiskLevel.HIGH
            else:
                result.risk_level = RiskLevel.CRITICAL
                result.flags.append("low_average_balance")

            # Check for negative indicators
            if nsf_count > 0:
                result.flags.append(f"nsf_count_{nsf_count}")
            if nsf_count > 3:
                result.status = CheckStatus.NEEDS_REVIEW

            if overdraft_count > 0:
                result.flags.append(f"overdraft_count_{overdraft_count}")

            # Check for fraud indicators
            large_deposits = details.get("large_deposits", [])
            if large_deposits:
                result.flags.append(f"large_deposits_{len(large_deposits)}")
                if len(large_deposits) > 2:
                    result.status = CheckStatus.NEEDS_REVIEW

            # Verify name matches
            if not details.get("name_match", True):
                result.flags.append("name_mismatch")
                result.status = CheckStatus.NEEDS_REVIEW

            # Check for document tampering
            if details.get("tampering_detected"):
                result.flags.append("possible_tampering")
                result.risk_level = RiskLevel.CRITICAL
                result.status = CheckStatus.NEEDS_REVIEW

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"Bank statement analysis failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # Document Verification (General)
    # =========================================================================
    async def verify_document(
        self,
        document_url: str,
        document_type: DocumentType,
        validation_data: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """
        General document verification.

        Performs:
        - Authenticity check (not forged/tampered)
        - Data extraction
        - Cross-validation with application data
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.DOCUMENT_ANALYSIS,
            status=CheckStatus.RUNNING,
            vendor="document-ai",
        )

        try:
            response = await self._make_request(
                "/document-verify",
                {
                    "document_url": document_url,
                    "document_type": document_type.value,
                    "validation_data": validation_data or {},
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("verified", False)

            details = response.get("details", {})
            confidence = details.get("confidence", 0.0)
            result.score = int(confidence * 100)

            # Assess based on confidence
            if confidence >= 0.95:
                result.risk_level = RiskLevel.LOW
            elif confidence >= 0.80:
                result.risk_level = RiskLevel.MEDIUM
            elif confidence >= 0.60:
                result.risk_level = RiskLevel.HIGH
                result.status = CheckStatus.NEEDS_REVIEW
            else:
                result.risk_level = RiskLevel.CRITICAL
                result.status = CheckStatus.NEEDS_REVIEW
                result.flags.append("low_confidence")

            # Check for fraud indicators
            fraud_indicators = details.get("fraud_indicators", [])
            for indicator in fraud_indicators:
                result.flags.append(f"fraud_{indicator}")

            if fraud_indicators:
                result.risk_level = RiskLevel.CRITICAL
                result.status = CheckStatus.NEEDS_REVIEW

            # Check data consistency
            mismatches = details.get("data_mismatches", [])
            for mismatch in mismatches:
                result.flags.append(f"mismatch_{mismatch}")

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"Document verification failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # Analyze Multiple Documents in Parallel
    # =========================================================================
    async def analyze_documents_parallel(
        self,
        documents: List[Dict[str, Any]],
        validation_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, CheckResult]:
        """
        Analyze multiple documents in parallel.

        Args:
            documents: List of dicts with 'url' and 'type' keys
            validation_data: Data to validate against

        Returns:
            Dict mapping document URLs to results
        """
        tasks = []
        urls = []

        for doc in documents:
            url = doc.get("url")
            doc_type_str = doc.get("type", "financial_statement")

            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.FINANCIAL_STATEMENT

            urls.append(url)

            if doc_type == DocumentType.BANK_STATEMENT:
                tasks.append(
                    self.analyze_bank_statement(
                        document_url=url,
                        expected_business_name=validation_data.get("business_name") if validation_data else None,
                        expected_account_holder=validation_data.get("account_holder") if validation_data else None,
                    )
                )
            else:
                tasks.append(
                    self.verify_document(
                        document_url=url,
                        document_type=doc_type,
                        validation_data=validation_data,
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        result_dict = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                result_dict[url] = CheckResult(
                    check_type=CheckType.DOCUMENT_ANALYSIS,
                    status=CheckStatus.FAILED,
                    error=str(result),
                )
            else:
                result_dict[url] = result

        return result_dict


# Singleton instance
document_analysis_service = DocumentAnalysisService()
