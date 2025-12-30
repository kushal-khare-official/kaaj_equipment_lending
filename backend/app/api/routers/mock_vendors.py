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
    """
    Fetch FICO score for a guarantor based on SSN/name.
    
    Test SSN patterns for different scenarios:
    - 111-11-1111: Excellent credit (FICO 780+)
    - 222-22-2222: Good credit (FICO 700-749)
    - 333-33-3333: Fair credit (FICO 650-699)
    - 444-44-4444: Poor credit (FICO 600-649)
    - 555-55-5555: Bad credit (FICO <600)
    - 666-66-6666: No credit history found
    - 777-77-7777: High utilization (95%)
    - 888-88-8888: Recent delinquencies
    - 999-99-9999: API failure
    - Default: Good credit (720)
    """
    ssn = payload.ssn if payload and payload.ssn else ""
    
    # Test scenarios based on SSN
    if "111-11-1111" in ssn or "11111111" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 785,
            "vendor": "mock-credit",
            "details": {
                "fico": 785,
                "report_date": "2025-12-29",
                "credit_utilization": 15,
                "accounts_open": 8,
                "delinquencies": 0,
                "bankruptcies": 0,
                "payment_history": "excellent",
            },
        }
    elif "222-22-2222" in ssn or "22222222" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 725,
            "vendor": "mock-credit",
            "details": {
                "fico": 725,
                "report_date": "2025-12-29",
                "credit_utilization": 30,
                "accounts_open": 6,
                "delinquencies": 0,
                "bankruptcies": 0,
                "payment_history": "good",
            },
        }
    elif "333-33-3333" in ssn or "33333333" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 670,
            "vendor": "mock-credit",
            "details": {
                "fico": 670,
                "report_date": "2025-12-29",
                "credit_utilization": 60,
                "accounts_open": 4,
                "delinquencies": 1,
                "bankruptcies": 0,
                "payment_history": "fair",
            },
        }
    elif "444-44-4444" in ssn or "44444444" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 620,
            "vendor": "mock-credit",
            "details": {
                "fico": 620,
                "report_date": "2025-12-29",
                "credit_utilization": 80,
                "accounts_open": 3,
                "delinquencies": 3,
                "bankruptcies": 0,
                "payment_history": "poor",
            },
        }
    elif "555-55-5555" in ssn or "55555555" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 540,
            "vendor": "mock-credit",
            "details": {
                "fico": 540,
                "report_date": "2025-12-29",
                "credit_utilization": 95,
                "accounts_open": 2,
                "delinquencies": 6,
                "bankruptcies": 1,
                "payment_history": "bad",
            },
        }
    elif "666-66-6666" in ssn or "66666666" in ssn.replace("-", ""):
        return {
            "status": "failed",
            "score": 0,
            "vendor": "mock-credit",
            "error": "No credit history found",
            "details": {},
        }
    elif "777-77-7777" in ssn or "77777777" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 680,
            "vendor": "mock-credit",
            "details": {
                "fico": 680,
                "report_date": "2025-12-29",
                "credit_utilization": 95,
                "accounts_open": 5,
                "delinquencies": 0,
                "bankruptcies": 0,
                "payment_history": "fair",
                "high_credit_utilization_flag": True,
            },
        }
    elif "888-88-8888" in ssn or "88888888" in ssn.replace("-", ""):
        return {
            "status": "success",
            "score": 650,
            "vendor": "mock-credit",
            "details": {
                "fico": 650,
                "report_date": "2025-12-29",
                "credit_utilization": 55,
                "accounts_open": 4,
                "delinquencies": 2,
                "recent_delinquency": "2025-10-15",
                "bankruptcies": 0,
                "payment_history": "fair",
            },
        }
    elif "999-99-9999" in ssn or "99999999" in ssn.replace("-", ""):
        return {
            "status": "failed",
            "vendor": "mock-credit",
            "error": "Credit bureau API temporarily unavailable",
            "details": {},
        }
    
    # Default good credit
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
    """
    Run KYC (Know Your Customer) check for a guarantor.
    
    Test SSN patterns for different scenarios:
    - 111-11-1111: Verified
    - 222-22-2222: Verified
    - 333-33-3333: Address mismatch
    - 444-44-4444: Identity verification failed
    - 555-55-5555: Watchlist hit
    - 666-66-6666: High fraud score
    - 999-99-9999: API failure
    - Default: Verified
    """
    ssn = payload.ssn if payload and payload.ssn else ""
    
    if "333-33-3333" in ssn or "33333333" in ssn.replace("-", ""):
        return {
            "status": "needs_review",
            "vendor": "mock-kyc",
            "verified": False,
            "details": {
                "identity_verified": True,
                "address_verified": False,
                "watchlist_clear": True,
                "fraud_score": 15,
                "address_mismatch_flag": True,
            },
        }
    elif "444-44-4444" in ssn or "44444444" in ssn.replace("-", ""):
        return {
            "status": "failed",
            "vendor": "mock-kyc",
            "verified": False,
            "error": "Identity verification failed",
            "details": {
                "identity_verified": False,
                "address_verified": False,
                "watchlist_clear": True,
                "fraud_score": 45,
            },
        }
    elif "555-55-5555" in ssn or "55555555" in ssn.replace("-", ""):
        return {
            "status": "needs_review",
            "vendor": "mock-kyc",
            "verified": False,
            "details": {
                "identity_verified": True,
                "address_verified": True,
                "watchlist_clear": False,
                "watchlist_hit": "OFAC sanctions list",
                "fraud_score": 85,
            },
        }
    elif "666-66-6666" in ssn or "66666666" in ssn.replace("-", ""):
        return {
            "status": "needs_review",
            "vendor": "mock-kyc",
            "verified": False,
            "details": {
                "identity_verified": True,
                "address_verified": True,
                "watchlist_clear": True,
                "fraud_score": 75,
                "high_fraud_score_flag": True,
            },
        }
    elif "999-99-9999" in ssn or "99999999" in ssn.replace("-", ""):
        return {
            "status": "failed",
            "vendor": "mock-kyc",
            "error": "KYC service temporarily unavailable",
            "details": {},
        }
    
    # Default verified
    return {
        "status": "success",
        "vendor": "mock-kyc",
        "verified": True,
        "details": {
            "identity_verified": True,
            "address_verified": True,
            "watchlist_clear": True,
            "fraud_score": 5,
        },
    }


@router.post("/kyb")
def kyb_check(payload: Optional[KYBRequest] = None):
    """
    Run KYB (Know Your Business) check and fetch PayNet score.
    
    Test business name patterns for different scenarios:
    - Contains "EXCELLENT": PayNet 850+, verified
    - Contains "GOOD": PayNet 750-799, verified
    - Contains "FAIR": PayNet 650-699, verified
    - Contains "POOR": PayNet 550-599, verified
    - Contains "STARTUP": PayNet N/A, new business (< 2 years)
    - Contains "INACTIVE": Business inactive
    - Contains "UNVERIFIED": TIN verification failed
    - Contains "FAIL": API failure
    - Default: PayNet 85, verified
    """
    business_name = payload.business_name.upper() if payload and payload.business_name else ""
    
    if "EXCELLENT" in business_name:
        return {
            "status": "success",
            "vendor": "mock-kyb",
            "verified": True,
            "paynet_score": 865,
            "details": {
                "business_verified": True,
                "tin_verified": True,
                "paynet_score": 865,
                "years_in_business": 12,
                "business_status": "active",
                "credit_grade": "A+",
                "revolving_utilization": 15,
            },
        }
    elif "GOOD" in business_name:
        return {
            "status": "success",
            "vendor": "mock-kyb",
            "verified": True,
            "paynet_score": 775,
            "details": {
                "business_verified": True,
                "tin_verified": True,
                "paynet_score": 775,
                "years_in_business": 7,
                "business_status": "active",
                "credit_grade": "A",
                "revolving_utilization": 35,
            },
        }
    elif "FAIR" in business_name:
        return {
            "status": "success",
            "vendor": "mock-kyb",
            "verified": True,
            "paynet_score": 670,
            "details": {
                "business_verified": True,
                "tin_verified": True,
                "paynet_score": 670,
                "years_in_business": 4,
                "business_status": "active",
                "credit_grade": "B",
                "revolving_utilization": 65,
            },
        }
    elif "POOR" in business_name:
        return {
            "status": "success",
            "vendor": "mock-kyb",
            "verified": True,
            "paynet_score": 580,
            "details": {
                "business_verified": True,
                "tin_verified": True,
                "paynet_score": 580,
                "years_in_business": 3,
                "business_status": "active",
                "credit_grade": "C",
                "revolving_utilization": 85,
                "delinquent_accounts": 2,
            },
        }
    elif "STARTUP" in business_name:
        return {
            "status": "success",
            "vendor": "mock-kyb",
            "verified": True,
            "paynet_score": 0,
            "details": {
                "business_verified": True,
                "tin_verified": True,
                "paynet_score": None,
                "years_in_business": 1,
                "business_status": "active",
                "credit_grade": "N/A",
                "is_startup": True,
            },
        }
    elif "INACTIVE" in business_name:
        return {
            "status": "needs_review",
            "vendor": "mock-kyb",
            "verified": False,
            "paynet_score": 0,
            "details": {
                "business_verified": False,
                "tin_verified": True,
                "business_status": "inactive",
                "status_date": "2024-06-15",
            },
        }
    elif "UNVERIFIED" in business_name:
        return {
            "status": "failed",
            "vendor": "mock-kyb",
            "verified": False,
            "error": "TIN verification failed",
            "paynet_score": 0,
            "details": {
                "business_verified": False,
                "tin_verified": False,
            },
        }
    elif "FAIL" in business_name:
        return {
            "status": "failed",
            "vendor": "mock-kyb",
            "error": "Business verification service temporarily unavailable",
            "details": {},
        }
    
    # Default verified
    return {
        "status": "success",
        "vendor": "mock-kyb",
        "verified": True,
        "paynet_score": 785,
        "details": {
            "business_verified": True,
            "tin_verified": True,
            "paynet_score": 785,
            "years_in_business": 5,
            "business_status": "active",
            "revolving_utilization": 40,
        },
    }


@router.post("/business-search")
def business_search(payload: Optional[BusinessSearchRequest] = None):
    """
    Search for businesses by name and return matching results.

    Test business name patterns for quick test scenarios:
    - EXCELLENT TRUCKING INC: Perfect application scenario
    - FAIR LOGISTICS LLC: Needs manual review scenario
    - POOR TRANSPORT CO: High risk scenario
    - NEW STARTUP DELIVERY: Startup scenario
    """
    business_name = (payload.business_name or "").upper() if payload else ""

    # All available test businesses
    all_businesses = [
        # Quick Test Scenario A: Perfect Application
        {
            "id": "biz_excellent_001",
            "legal_name": "EXCELLENT TRUCKING INC",
            "city": "Dallas",
            "state": "TX",
        },
        # Quick Test Scenario B: Needs Manual Review
        {
            "id": "biz_fair_001",
            "legal_name": "FAIR LOGISTICS LLC",
            "city": "Atlanta",
            "state": "GA",
        },
        # Quick Test Scenario C: High Risk
        {
            "id": "biz_poor_001",
            "legal_name": "POOR TRANSPORT CO",
            "city": "Detroit",
            "state": "MI",
        },
        # Quick Test Scenario D: Startup
        {
            "id": "biz_startup_001",
            "legal_name": "NEW STARTUP DELIVERY",
            "city": "Austin",
            "state": "TX",
        },
        # Standard test businesses
        {
            "id": "biz_good_001",
            "legal_name": "GOOD FREIGHT SOLUTIONS",
            "city": "Denver",
            "state": "CO",
        },
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
    results = all_businesses
    if business_name:
        results = [r for r in all_businesses if business_name in r["legal_name"].upper()]

    return {
        "status": "success",
        "vendor": "mock-biz",
        "results": results,
    }


@router.post("/business-prefill")
def business_prefill(payload: Optional[BusinessSelectRequest] = None):
    """
    Get full business details for a selected business ID.

    Test scenario business IDs:
    - biz_excellent_001: Perfect application (use SSN 111-11-1111)
    - biz_fair_001: Needs manual review (use SSN 333-33-3333)
    - biz_poor_001: High risk (use SSN 555-55-5555)
    - biz_startup_001: Startup (use SSN 222-22-2222)
    """
    business_id = payload.business_id if payload else "biz_001"

    # Mock database of business details
    businesses = {
        # Quick Test Scenario A: Perfect Application
        "biz_excellent_001": {
            "legal_name": "EXCELLENT TRUCKING INC",
            "dba": "Excellence Transport",
            "address": {
                "street": "1500 Commerce Drive",
                "city": "Dallas",
                "state": "TX",
                "zip": "75201",
            },
            "phone": "(214) 555-1000",
            "email": "info@excellenttrucking.com",
            "tin": "75-1234567",
            "formation_date": "2012-03-20",
            "entity_type": "Corporation",
            "guarantors": [
                {
                    "first_name": "David",
                    "last_name": "Excellence",
                    "title": "CEO",
                    "ownership_pct": 75,
                    "address": {
                        "street": "2500 Park Lane",
                        "city": "Dallas",
                        "state": "TX",
                        "zip": "75205",
                    },
                    "phone": "(214) 555-1001",
                    "email": "david@excellenttrucking.com",
                    "ssn_last4": "1111",
                },
                {
                    "first_name": "Mary",
                    "last_name": "Excellence",
                    "title": "CFO",
                    "ownership_pct": 25,
                    "address": {
                        "street": "2500 Park Lane",
                        "city": "Dallas",
                        "state": "TX",
                        "zip": "75205",
                    },
                    "phone": "(214) 555-1002",
                    "email": "mary@excellenttrucking.com",
                    "ssn_last4": "2222",
                },
            ],
        },
        # Quick Test Scenario B: Needs Manual Review
        "biz_fair_001": {
            "legal_name": "FAIR LOGISTICS LLC",
            "dba": "Fair Logistics",
            "address": {
                "street": "500 Industrial Way",
                "city": "Atlanta",
                "state": "GA",
                "zip": "30301",
            },
            "phone": "(404) 555-2000",
            "email": "info@fairlogistics.com",
            "tin": "58-2345678",
            "formation_date": "2020-06-15",
            "entity_type": "LLC",
            "guarantors": [
                {
                    "first_name": "Steve",
                    "last_name": "Fairbanks",
                    "title": "Managing Member",
                    "ownership_pct": 100,
                    "address": {
                        "street": "123 Peachtree St",
                        "city": "Atlanta",
                        "state": "GA",
                        "zip": "30303",
                    },
                    "phone": "(404) 555-2001",
                    "email": "steve@fairlogistics.com",
                    "ssn_last4": "3333",
                },
            ],
        },
        # Quick Test Scenario C: High Risk
        "biz_poor_001": {
            "legal_name": "POOR TRANSPORT CO",
            "dba": "Poor Transport",
            "address": {
                "street": "1000 Detroit Ave",
                "city": "Detroit",
                "state": "MI",
                "zip": "48201",
            },
            "phone": "(313) 555-3000",
            "email": "info@poortransport.com",
            "tin": "38-3456789",
            "formation_date": "2021-09-01",
            "entity_type": "Corporation",
            "guarantors": [
                {
                    "first_name": "Rick",
                    "last_name": "Poorman",
                    "title": "President",
                    "ownership_pct": 100,
                    "address": {
                        "street": "500 Woodward Ave",
                        "city": "Detroit",
                        "state": "MI",
                        "zip": "48226",
                    },
                    "phone": "(313) 555-3001",
                    "email": "rick@poortransport.com",
                    "ssn_last4": "5555",
                },
            ],
        },
        # Quick Test Scenario D: Startup
        "biz_startup_001": {
            "legal_name": "NEW STARTUP DELIVERY",
            "dba": "Startup Delivery",
            "address": {
                "street": "100 Tech Row",
                "city": "Austin",
                "state": "TX",
                "zip": "78701",
            },
            "phone": "(512) 555-4000",
            "email": "info@startupdelivery.com",
            "tin": "84-4567890",
            "formation_date": "2024-01-15",  # Very recent - startup
            "entity_type": "LLC",
            "guarantors": [
                {
                    "first_name": "Emily",
                    "last_name": "Startup",
                    "title": "Founder",
                    "ownership_pct": 60,
                    "address": {
                        "street": "200 Congress Ave",
                        "city": "Austin",
                        "state": "TX",
                        "zip": "78701",
                    },
                    "phone": "(512) 555-4001",
                    "email": "emily@startupdelivery.com",
                    "ssn_last4": "2222",  # Good credit
                },
                {
                    "first_name": "Jason",
                    "last_name": "Cofounder",
                    "title": "Co-Founder",
                    "ownership_pct": 40,
                    "address": {
                        "street": "300 6th Street",
                        "city": "Austin",
                        "state": "TX",
                        "zip": "78702",
                    },
                    "phone": "(512) 555-4002",
                    "email": "jason@startupdelivery.com",
                    "ssn_last4": "1111",  # Excellent credit
                },
            ],
        },
        # Standard test businesses
        "biz_good_001": {
            "legal_name": "GOOD FREIGHT SOLUTIONS",
            "dba": "Good Freight",
            "address": {
                "street": "750 Market Street",
                "city": "Denver",
                "state": "CO",
                "zip": "80202",
            },
            "phone": "(303) 555-5000",
            "email": "info@goodfreight.com",
            "tin": "84-5678901",
            "formation_date": "2018-04-10",
            "entity_type": "Corporation",
            "guarantors": [
                {
                    "first_name": "Michael",
                    "last_name": "Goodman",
                    "title": "CEO",
                    "ownership_pct": 100,
                    "address": {
                        "street": "900 Larimer St",
                        "city": "Denver",
                        "state": "CO",
                        "zip": "80204",
                    },
                    "phone": "(303) 555-5001",
                    "email": "michael@goodfreight.com",
                    "ssn_last4": "2222",
                },
            ],
        },
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


class BankVerificationRequest(BaseModel):
    account_number: Optional[str] = None
    routing_number: Optional[str] = None


class OnlinePresenceRequest(BaseModel):
    business_name: Optional[str] = None
    website: Optional[str] = None


class UCCSearchRequest(BaseModel):
    business_name: Optional[str] = None
    state: Optional[str] = None


class DocumentClassifyRequest(BaseModel):
    document_url: str


class DocumentVerifyRequest(BaseModel):
    document_url: str
    document_type: str
    validation_data: Optional[dict] = None


class BankStatementAnalysisRequest(BaseModel):
    document_url: str
    expected_business_name: Optional[str] = None
    expected_account_holder: Optional[str] = None


@router.post("/bank-verification")
def bank_verification(payload: Optional[BankVerificationRequest] = None):
    """Verify bank account and return balance information."""
    return {
        "status": "success",
        "vendor": "mock-bank",
        "balance": 100000,
        "details": {
            "account_verified": True,
            "account_type": "business_checking",
            "account_status": "active",
            "average_daily_balance": 85000,
        },
    }


@router.post("/online-presence")
def online_presence_check(payload: Optional[OnlinePresenceRequest] = None):
    """Verify business online presence including website and social media."""
    return {
        "status": "success",
        "vendor": "mock-online-presence",
        "verified": True,
        "details": {
            "website_active": True,
            "website_url": payload.website if payload and payload.website else "https://example.com",
            "ssl_valid": True,
            "domain_age_months": 36,
            "social_media": {
                "linkedin": True,
                "facebook": True,
                "twitter": False,
            },
            "business_listings": {
                "google_business": True,
                "yelp": True,
                "bbb": False,
            },
            "reviews_count": 45,
            "average_rating": 4.5,
        },
    }


@router.post("/ucc-search")
def ucc_search(payload: Optional[UCCSearchRequest] = None):
    """Search for UCC liens on the business."""
    return {
        "status": "success",
        "vendor": "mock-ucc-search",
        "liens": [
            {
                "filing_number": "UCC-2023-123456",
                "secured_party": "ABC Finance Corp",
                "filing_date": "2023-06-15",
                "collateral_description": "All business assets",
                "status": "active",
            },
        ],
        "judgments": [],
        "tax_liens": [],
    }


@router.post("/document-classify")
def document_classify(payload: DocumentClassifyRequest):
    """Classify document type using AI vision."""
    # Mock classification based on URL patterns
    url = payload.document_url.lower()

    if "bank" in url or "statement" in url:
        doc_type = "bank_statement"
        confidence = 0.95
    elif "tax" in url or "1040" in url or "return" in url:
        doc_type = "tax_return"
        confidence = 0.92
    elif "license" in url or "dl" in url or "driver" in url:
        doc_type = "drivers_license"
        confidence = 0.98
    elif "invoice" in url or "equipment" in url:
        doc_type = "equipment_invoice"
        confidence = 0.89
    else:
        doc_type = "financial_statement"
        confidence = 0.75

    return {
        "status": "success",
        "vendor": "mock-document-ai",
        "document_type": doc_type,
        "confidence": confidence,
        "extracted_data": {
            "page_count": 3,
            "has_signature": True,
            "date_detected": "2024-12-01",
        },
        "validation_flags": [],
        "fraud_indicators": [],
        "summary": f"Document classified as {doc_type} with {confidence:.0%} confidence",
    }


@router.post("/document-verify")
def document_verify(payload: DocumentVerifyRequest):
    """Verify document authenticity and extract data."""
    return {
        "status": "success",
        "vendor": "mock-document-ai",
        "verified": True,
        "details": {
            "confidence": 0.92,
            "authenticity_score": 0.95,
            "tampering_detected": False,
            "fraud_indicators": [],
            "data_mismatches": [],
            "extracted_fields": {
                "document_date": "2024-12-01",
                "issuer": "Sample Bank",
                "recipient": payload.validation_data.get("business_name") if payload.validation_data else "Unknown",
            },
        },
    }


@router.post("/bank-statement-analysis")
def bank_statement_analysis(payload: BankStatementAnalysisRequest):
    """
    Analyze bank statements for underwriting.
    
    Test URL patterns for different scenarios:
    - Contains "excellent": Strong cash flow, high balance
    - Contains "good": Good cash flow, moderate balance
    - Contains "fair": Acceptable cash flow, lower balance
    - Contains "poor": Weak cash flow, low balance
    - Contains "nsf": Multiple NSF fees
    - Contains "overdraft": Frequent overdrafts
    - Contains "mismatch": Name mismatch detected
    - Contains "tampered": Possible tampering detected
    - Default: Good cash flow
    """
    url = payload.document_url.lower()
    
    if "excellent" in url:
        return {
            "status": "success",
            "vendor": "mock-bank-statement-ai",
            "verified": True,
            "details": {
                "account_holder": payload.expected_account_holder or "John Smith",
                "bank_name": "First National Bank",
                "account_type": "Business Checking",
                "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
                "average_daily_balance": 250000,
                "ending_balance": 285000,
                "monthly_deposits": 450000,
                "monthly_withdrawals": 415000,
                "deposit_count": 22,
                "withdrawal_count": 38,
                "nsf_count": 0,
                "overdraft_count": 0,
                "negative_days": 0,
                "name_match": True,
                "tampering_detected": False,
                "revenue_estimate": 5400000,
                "cash_flow_grade": "A+",
            },
        }
    elif "good" in url:
        return {
            "status": "success",
            "vendor": "mock-bank-statement-ai",
            "verified": True,
            "details": {
                "account_holder": payload.expected_account_holder or "John Smith",
                "bank_name": "First National Bank",
                "account_type": "Business Checking",
                "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
                "average_daily_balance": 125000,
                "ending_balance": 142000,
                "monthly_deposits": 220000,
                "monthly_withdrawals": 203000,
                "deposit_count": 18,
                "withdrawal_count": 42,
                "nsf_count": 0,
                "overdraft_count": 0,
                "negative_days": 0,
                "name_match": True,
                "tampering_detected": False,
                "revenue_estimate": 2640000,
                "cash_flow_grade": "A",
            },
        }
    elif "fair" in url:
        return {
            "status": "success",
            "vendor": "mock-bank-statement-ai",
            "verified": True,
            "details": {
                "account_holder": payload.expected_account_holder or "John Smith",
                "bank_name": "Community Bank",
                "account_type": "Business Checking",
                "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
                "average_daily_balance": 45000,
                "ending_balance": 52000,
                "monthly_deposits": 95000,
                "monthly_withdrawals": 88000,
                "deposit_count": 12,
                "withdrawal_count": 35,
                "nsf_count": 0,
                "overdraft_count": 1,
                "negative_days": 2,
                "name_match": True,
                "tampering_detected": False,
                "revenue_estimate": 1140000,
                "cash_flow_grade": "B",
            },
        }
    elif "poor" in url:
        return {
            "status": "success",
            "vendor": "mock-bank-statement-ai",
            "verified": True,
            "details": {
                "account_holder": payload.expected_account_holder or "John Smith",
                "bank_name": "Local Bank",
                "account_type": "Business Checking",
                "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
                "average_daily_balance": 15000,
                "ending_balance": 8500,
                "monthly_deposits": 45000,
                "monthly_withdrawals": 51500,
                "deposit_count": 8,
                "withdrawal_count": 42,
                "nsf_count": 2,
                "overdraft_count": 5,
                "negative_days": 8,
                "name_match": True,
                "tampering_detected": False,
                "revenue_estimate": 540000,
                "cash_flow_grade": "C",
            },
        }
    elif "nsf" in url:
        return {
            "status": "needs_review",
            "vendor": "mock-bank-statement-ai",
            "verified": True,
            "details": {
                "account_holder": payload.expected_account_holder or "John Smith",
                "bank_name": "Regional Bank",
                "account_type": "Business Checking",
                "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
                "average_daily_balance": 12000,
                "ending_balance": 9500,
                "monthly_deposits": 55000,
                "monthly_withdrawals": 57500,
                "deposit_count": 10,
                "withdrawal_count": 45,
                "nsf_count": 7,
                "overdraft_count": 12,
                "negative_days": 12,
                "name_match": True,
                "tampering_detected": False,
                "revenue_estimate": 660000,
                "cash_flow_grade": "D",
                "high_nsf_flag": True,
            },
        }
    elif "mismatch" in url:
        return {
            "status": "needs_review",
            "vendor": "mock-bank-statement-ai",
            "verified": False,
            "details": {
                "account_holder": "Different Name LLC",
                "bank_name": "First National Bank",
                "account_type": "Business Checking",
                "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
                "average_daily_balance": 75000,
                "ending_balance": 82000,
                "name_match": False,
                "name_mismatch_flag": True,
                "tampering_detected": False,
            },
        }
    elif "tampered" in url:
        return {
            "status": "failed",
            "vendor": "mock-bank-statement-ai",
            "verified": False,
            "error": "Possible document tampering detected",
            "details": {
                "tampering_detected": True,
                "tampering_indicators": [
                    "Inconsistent fonts detected",
                    "Suspicious number alignment",
                    "Digital alterations found",
                ],
            },
        }
    
    # Default good scenario
    return {
        "status": "success",
        "vendor": "mock-bank-statement-ai",
        "verified": True,
        "details": {
            "account_holder": payload.expected_account_holder or "John Smith",
            "bank_name": "First National Bank",
            "account_type": "Business Checking",
            "statement_period": {"start": "2024-11-01", "end": "2024-11-30"},
            "average_daily_balance": 75000,
            "ending_balance": 82500,
            "monthly_deposits": 125000,
            "monthly_withdrawals": 118500,
            "deposit_count": 15,
            "withdrawal_count": 42,
            "nsf_count": 0,
            "overdraft_count": 0,
            "negative_days": 0,
            "name_match": True,
            "tampering_detected": False,
            "revenue_estimate": 1500000,
            "cash_flow_grade": "A",
        },
    }


@router.get("/status")
def status():
    """Health check for all vendor services."""
    return {
        "credit": {"status": "ready"},
        "kyc": {"status": "ready"},
        "kyb": {"status": "ready"},
        "business_prefill": {"status": "ready"},
        "bank_verification": {"status": "ready"},
        "online_presence": {"status": "ready"},
        "ucc_search": {"status": "ready"},
        "document_classify": {"status": "ready"},
        "document_verify": {"status": "ready"},
        "bank_statement_analysis": {"status": "ready"},
    }
