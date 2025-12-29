from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/mock", tags=["mock-vendors"])


class CreditCheckRequest(BaseModel):
    ssn: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class KYCRequest(BaseModel):
    ssn: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None


class KYBRequest(BaseModel):
    business_name: Optional[str] = None
    tin: Optional[str] = None


class BusinessSearchRequest(BaseModel):
    business_name: Optional[str] = None


class BusinessSelectRequest(BaseModel):
    business_id: str


@router.post("/credit-check")
def credit_check(payload: Optional[CreditCheckRequest] = None):
    """Fetch FICO score for a guarantor based on SSN/name."""
    return {
        "status": "success",
        "score": 720,
        "vendor": "mock-credit",
        "details": {
            "fico": 720,
            "report_date": "2025-12-29",
            "credit_utilization": 35,
            "accounts_open": 5,
            "delinquencies": 0,
        },
    }


@router.post("/kyc")
def kyc_check(payload: Optional[KYCRequest] = None):
    """Run KYC (Know Your Customer) check for a guarantor."""
    return {
        "status": "success",
        "vendor": "mock-kyc",
        "verified": True,
        "details": {
            "identity_verified": True,
            "address_verified": True,
            "watchlist_clear": True,
            "fraud_score": 0,
        },
    }


@router.post("/kyb")
def kyb_check(payload: Optional[KYBRequest] = None):
    """Run KYB (Know Your Business) check and fetch PayNet score."""
    return {
        "status": "success",
        "vendor": "mock-kyb",
        "verified": True,
        "paynet_score": 85,
        "details": {
            "business_verified": True,
            "tin_verified": True,
            "paynet_score": 85,
            "years_in_business": 5,
            "business_status": "active",
        },
    }


@router.post("/business-search")
def business_search(payload: Optional[BusinessSearchRequest] = None):
    """Search for businesses by name and return matching results."""
    business_name = (payload.business_name or "").upper() if payload else ""

    # Return mock search results - multiple businesses matching the search
    results = [
        {
            "id": "biz_001",
            "legal_name": "KAAJ TECHNOLOGIES INC.",
            "city": "Minneapolis",
            "state": "MN",
        },
        {
            "id": "biz_002",
            "legal_name": "KAAJ TECH SOLUTIONS LLC",
            "city": "St. Paul",
            "state": "MN",
        },
        {
            "id": "biz_003",
            "legal_name": "KAAJ INDUSTRIES CORP",
            "city": "Chicago",
            "state": "IL",
        },
    ]

    # Filter results based on search term (case-insensitive)
    if business_name:
        results = [r for r in results if business_name in r["legal_name"].upper()]

    return {
        "status": "success",
        "vendor": "mock-biz",
        "results": results,
    }


@router.post("/business-prefill")
def business_prefill(payload: Optional[BusinessSelectRequest] = None):
    """Get full business details for a selected business ID."""
    business_id = payload.business_id if payload else "biz_001"

    # Mock database of business details
    businesses = {
        "biz_001": {
            "legal_name": "KAAJ TECHNOLOGIES INC.",
            "dba": "Kaaj Tech",
            "address": {
                "street": "123 Business Ave",
                "city": "Minneapolis",
                "state": "MN",
                "zip": "55401",
            },
            "phone": "(612) 555-1234",
            "email": "info@kaajtech.com",
            "tin": "12-3456789",
            "formation_date": "2019-03-15",
            "entity_type": "Corporation",
            "guarantors": [
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "title": "CEO",
                    "ownership_pct": 60,
                    "address": {
                        "street": "456 Residence St",
                        "city": "Minneapolis",
                        "state": "MN",
                        "zip": "55402",
                    },
                    "phone": "(612) 555-5678",
                    "email": "john.smith@kaajtech.com",
                    "ssn_last4": "1234",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "title": "CFO",
                    "ownership_pct": 40,
                    "address": {
                        "street": "789 Home Ave",
                        "city": "St. Paul",
                        "state": "MN",
                        "zip": "55101",
                    },
                    "phone": "(651) 555-9012",
                    "email": "jane.doe@kaajtech.com",
                    "ssn_last4": "5678",
                },
            ],
        },
        "biz_002": {
            "legal_name": "KAAJ TECH SOLUTIONS LLC",
            "dba": "KTS",
            "address": {
                "street": "500 Innovation Way",
                "city": "St. Paul",
                "state": "MN",
                "zip": "55102",
            },
            "phone": "(651) 555-2000",
            "email": "contact@kaajtechsolutions.com",
            "tin": "45-6789012",
            "formation_date": "2021-06-01",
            "entity_type": "LLC",
            "guarantors": [
                {
                    "first_name": "Michael",
                    "last_name": "Johnson",
                    "title": "Managing Member",
                    "ownership_pct": 100,
                    "address": {
                        "street": "1200 Summit Ave",
                        "city": "St. Paul",
                        "state": "MN",
                        "zip": "55105",
                    },
                    "phone": "(651) 555-3000",
                    "email": "michael.j@kaajtechsolutions.com",
                    "ssn_last4": "9876",
                },
            ],
        },
        "biz_003": {
            "legal_name": "KAAJ INDUSTRIES CORP",
            "dba": "Kaaj Industries",
            "address": {
                "street": "789 Industrial Blvd",
                "city": "Chicago",
                "state": "IL",
                "zip": "60601",
            },
            "phone": "(312) 555-4000",
            "email": "info@kaajindustries.com",
            "tin": "78-9012345",
            "formation_date": "2015-01-15",
            "entity_type": "Corporation",
            "guarantors": [
                {
                    "first_name": "Sarah",
                    "last_name": "Williams",
                    "title": "President",
                    "ownership_pct": 50,
                    "address": {
                        "street": "2500 Lake Shore Dr",
                        "city": "Chicago",
                        "state": "IL",
                        "zip": "60614",
                    },
                    "phone": "(312) 555-5000",
                    "email": "sarah.w@kaajindustries.com",
                    "ssn_last4": "4321",
                },
                {
                    "first_name": "Robert",
                    "last_name": "Brown",
                    "title": "VP Operations",
                    "ownership_pct": 50,
                    "address": {
                        "street": "100 Michigan Ave",
                        "city": "Chicago",
                        "state": "IL",
                        "zip": "60602",
                    },
                    "phone": "(312) 555-6000",
                    "email": "robert.b@kaajindustries.com",
                    "ssn_last4": "8765",
                },
            ],
        },
    }

    data = businesses.get(business_id, businesses["biz_001"])

    return {
        "status": "success",
        "vendor": "mock-biz",
        "data": data,
    }


@router.post("/bank-verification")
def bank_verification():
    return {"status": "success", "vendor": "mock-bank", "balance": 100000}


@router.get("/status")
def status():
    return {
        "credit": {"status": "ready"},
        "kyc": {"status": "ready"},
        "kyb": {"status": "ready"},
        "business_prefill": {"status": "ready"},
        "bank_verification": {"status": "ready"},
    }
