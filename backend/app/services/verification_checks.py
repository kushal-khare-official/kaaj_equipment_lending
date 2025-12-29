"""
Verification check implementations for the lender matching platform.

Each check is designed to:
1. Call external vendor APIs (mocked in development)
2. Handle retries with exponential backoff
3. Return structured CheckResult objects
4. Support parallel execution via asyncio
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any

import httpx

from app.shared.workflow_enums import (
    CheckType,
    CheckStatus,
    CheckResult,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# Configuration
VENDOR_BASE_URL = "http://localhost:8000/mock"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds


class VerificationService:
    """
    Service for running verification checks against external vendors.

    Supports:
    - Async execution for parallel check processing
    - Automatic retries with exponential backoff
    - Structured result formatting
    - Risk level assessment
    """

    def __init__(self, base_url: str = VENDOR_BASE_URL):
        self.base_url = base_url

    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """Make an HTTP request to a vendor endpoint with retry logic."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=payload,
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as e:
                last_error = f"Timeout on attempt {attempt + 1}: {str(e)}"
                logger.warning(f"Request to {endpoint} timed out (attempt {attempt + 1})")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP error {e.response.status_code}: {str(e)}"
                logger.warning(f"HTTP error on {endpoint}: {e.response.status_code}")
                if e.response.status_code < 500:
                    # Don't retry client errors
                    raise
            except Exception as e:
                last_error = f"Request failed: {str(e)}"
                logger.warning(f"Request to {endpoint} failed: {str(e)}")

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

        raise Exception(last_error)

    # =========================================================================
    # KYC - Know Your Customer
    # =========================================================================
    async def run_kyc_check(
        self,
        ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> CheckResult:
        """
        Run KYC (Know Your Customer) verification.

        Verifies:
        - Identity matches SSN
        - Address verification
        - Watchlist/sanctions screening
        - Fraud risk scoring
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.KYC,
            status=CheckStatus.RUNNING,
            vendor="kyc-vendor",
        )

        try:
            response = await self._make_request(
                "/kyc",
                {
                    "ssn": ssn,
                    "first_name": first_name,
                    "last_name": last_name,
                    "address": address,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("verified", False)

            details = response.get("details", {})
            fraud_score = details.get("fraud_score", 0)

            # Assess risk based on fraud score
            if fraud_score == 0:
                result.risk_level = RiskLevel.LOW
            elif fraud_score < 30:
                result.risk_level = RiskLevel.MEDIUM
            elif fraud_score < 70:
                result.risk_level = RiskLevel.HIGH
            else:
                result.risk_level = RiskLevel.CRITICAL
                result.flags.append("high_fraud_score")

            # Add flags for verification failures
            if not details.get("identity_verified"):
                result.flags.append("identity_not_verified")
                result.status = CheckStatus.NEEDS_REVIEW
            if not details.get("address_verified"):
                result.flags.append("address_not_verified")
            if not details.get("watchlist_clear"):
                result.flags.append("watchlist_hit")
                result.risk_level = RiskLevel.CRITICAL
                result.status = CheckStatus.NEEDS_REVIEW

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"KYC check failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # KYB - Know Your Business
    # =========================================================================
    async def run_kyb_check(
        self,
        business_name: Optional[str] = None,
        tin: Optional[str] = None,
    ) -> CheckResult:
        """
        Run KYB (Know Your Business) verification.

        Verifies:
        - Business registration
        - TIN/EIN verification
        - Business status (active/inactive)
        - PayNet business credit score
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.KYB,
            status=CheckStatus.RUNNING,
            vendor="kyb-vendor",
        )

        try:
            response = await self._make_request(
                "/kyb",
                {
                    "business_name": business_name,
                    "tin": tin,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("verified", False)

            details = response.get("details", {})
            paynet_score = details.get("paynet_score", 0)
            result.score = paynet_score

            # Assess risk based on PayNet score
            if paynet_score >= 80:
                result.risk_level = RiskLevel.LOW
            elif paynet_score >= 60:
                result.risk_level = RiskLevel.MEDIUM
            elif paynet_score >= 40:
                result.risk_level = RiskLevel.HIGH
            else:
                result.risk_level = RiskLevel.CRITICAL
                result.flags.append("low_paynet_score")

            # Add flags for verification failures
            if not details.get("business_verified"):
                result.flags.append("business_not_verified")
                result.status = CheckStatus.NEEDS_REVIEW
            if not details.get("tin_verified"):
                result.flags.append("tin_not_verified")
                result.status = CheckStatus.NEEDS_REVIEW
            if details.get("business_status") != "active":
                result.flags.append("business_not_active")
                result.status = CheckStatus.NEEDS_REVIEW

            # Check years in business for startup flag
            years_in_business = details.get("years_in_business", 0)
            if years_in_business < 2:
                result.flags.append("startup_business")

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"KYB check failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # Credit Check (Personal)
    # =========================================================================
    async def run_credit_check(
        self,
        ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> CheckResult:
        """
        Run personal credit check (FICO score).

        Returns:
        - FICO score
        - Credit utilization
        - Account information
        - Delinquency history
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.CREDIT_CHECK,
            status=CheckStatus.RUNNING,
            vendor="credit-bureau",
        )

        try:
            response = await self._make_request(
                "/credit-check",
                {
                    "ssn": ssn,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("status") == "success"

            details = response.get("details", {})
            fico_score = details.get("fico", 0)
            result.score = fico_score

            # Assess risk based on FICO score
            if fico_score >= 720:
                result.risk_level = RiskLevel.LOW
            elif fico_score >= 680:
                result.risk_level = RiskLevel.MEDIUM
            elif fico_score >= 620:
                result.risk_level = RiskLevel.HIGH
            else:
                result.risk_level = RiskLevel.CRITICAL
                result.flags.append("low_fico_score")

            # Check for negative indicators
            delinquencies = details.get("delinquencies", 0)
            if delinquencies > 0:
                result.flags.append(f"delinquencies_{delinquencies}")
                if delinquencies > 2:
                    result.status = CheckStatus.NEEDS_REVIEW

            credit_utilization = details.get("credit_utilization", 0)
            if credit_utilization > 80:
                result.flags.append("high_credit_utilization")

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"Credit check failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # Bank Verification
    # =========================================================================
    async def run_bank_verification(
        self,
        account_number: Optional[str] = None,
        routing_number: Optional[str] = None,
    ) -> CheckResult:
        """
        Run bank account verification.

        Verifies:
        - Account exists and is active
        - Account ownership
        - Current balance
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.BANK_VERIFICATION,
            status=CheckStatus.RUNNING,
            vendor="bank-vendor",
        )

        try:
            response = await self._make_request(
                "/bank-verification",
                {
                    "account_number": account_number,
                    "routing_number": routing_number,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("status") == "success"

            balance = response.get("balance", 0)
            result.score = balance

            # Assess risk based on balance
            if balance >= 50000:
                result.risk_level = RiskLevel.LOW
            elif balance >= 10000:
                result.risk_level = RiskLevel.MEDIUM
            elif balance >= 1000:
                result.risk_level = RiskLevel.HIGH
            else:
                result.risk_level = RiskLevel.CRITICAL
                result.flags.append("low_bank_balance")

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"Bank verification failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # Online Presence Check
    # =========================================================================
    async def run_online_presence_check(
        self,
        business_name: Optional[str] = None,
        website: Optional[str] = None,
    ) -> CheckResult:
        """
        Verify business online presence.

        Checks:
        - Website exists and is operational
        - Social media presence
        - Business listing verification
        - Domain age
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.ONLINE_PRESENCE,
            status=CheckStatus.RUNNING,
            vendor="online-presence-vendor",
        )

        try:
            response = await self._make_request(
                "/online-presence",
                {
                    "business_name": business_name,
                    "website": website,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("verified", False)

            details = response.get("details", {})

            # Calculate presence score
            presence_score = 0
            if details.get("website_active"):
                presence_score += 40
            if details.get("social_media"):
                presence_score += 30
            if details.get("business_listings"):
                presence_score += 30

            result.score = presence_score

            # Assess risk
            if presence_score >= 70:
                result.risk_level = RiskLevel.LOW
            elif presence_score >= 40:
                result.risk_level = RiskLevel.MEDIUM
            else:
                result.risk_level = RiskLevel.HIGH
                result.flags.append("weak_online_presence")

            domain_age_months = details.get("domain_age_months", 0)
            if domain_age_months < 6:
                result.flags.append("new_domain")

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"Online presence check failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # UCC Lien Search
    # =========================================================================
    async def run_ucc_search(
        self,
        business_name: Optional[str] = None,
        state: Optional[str] = None,
    ) -> CheckResult:
        """
        Run UCC (Uniform Commercial Code) lien search.

        Searches for:
        - Existing liens on business assets
        - Prior security interests
        - Judgments
        """
        start_time = time.time()
        result = CheckResult(
            check_type=CheckType.UCC_SEARCH,
            status=CheckStatus.RUNNING,
            vendor="ucc-search-vendor",
        )

        try:
            response = await self._make_request(
                "/ucc-search",
                {
                    "business_name": business_name,
                    "state": state,
                },
            )

            result.raw_response = response
            result.status = CheckStatus.COMPLETED
            result.verified = response.get("status") == "success"

            liens = response.get("liens", [])
            result.score = len(liens)

            # Assess risk based on existing liens
            if len(liens) == 0:
                result.risk_level = RiskLevel.LOW
            elif len(liens) <= 2:
                result.risk_level = RiskLevel.MEDIUM
                result.flags.append(f"existing_liens_{len(liens)}")
            else:
                result.risk_level = RiskLevel.HIGH
                result.flags.append(f"multiple_liens_{len(liens)}")
                result.status = CheckStatus.NEEDS_REVIEW

        except Exception as e:
            result.status = CheckStatus.FAILED
            result.error = str(e)
            logger.error(f"UCC search failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # Run Multiple Checks in Parallel
    # =========================================================================
    async def run_checks_parallel(
        self,
        checks: list,
        application_data: Dict[str, Any],
    ) -> Dict[str, CheckResult]:
        """
        Run multiple verification checks in parallel.

        Args:
            checks: List of CheckType enums to run
            application_data: Application data for checks

        Returns:
            Dict mapping check type to result
        """
        tasks = []

        for check_type in checks:
            if check_type == CheckType.KYC:
                tasks.append(
                    self.run_kyc_check(
                        ssn=application_data.get("ssn"),
                        first_name=application_data.get("first_name"),
                        last_name=application_data.get("last_name"),
                        address=application_data.get("address"),
                    )
                )
            elif check_type == CheckType.KYB:
                tasks.append(
                    self.run_kyb_check(
                        business_name=application_data.get("business_name"),
                        tin=application_data.get("tin"),
                    )
                )
            elif check_type == CheckType.CREDIT_CHECK:
                tasks.append(
                    self.run_credit_check(
                        ssn=application_data.get("ssn"),
                        first_name=application_data.get("first_name"),
                        last_name=application_data.get("last_name"),
                    )
                )
            elif check_type == CheckType.BANK_VERIFICATION:
                tasks.append(
                    self.run_bank_verification(
                        account_number=application_data.get("account_number"),
                        routing_number=application_data.get("routing_number"),
                    )
                )
            elif check_type == CheckType.ONLINE_PRESENCE:
                tasks.append(
                    self.run_online_presence_check(
                        business_name=application_data.get("business_name"),
                        website=application_data.get("website"),
                    )
                )
            elif check_type == CheckType.UCC_SEARCH:
                tasks.append(
                    self.run_ucc_search(
                        business_name=application_data.get("business_name"),
                        state=application_data.get("state"),
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back to check types
        result_dict = {}
        for check_type, result in zip(checks, results):
            if isinstance(result, Exception):
                result_dict[check_type.value] = CheckResult(
                    check_type=check_type,
                    status=CheckStatus.FAILED,
                    error=str(result),
                )
            else:
                result_dict[check_type.value] = result

        return result_dict


# Singleton instance
verification_service = VerificationService()
