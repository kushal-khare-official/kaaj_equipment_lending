from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["mock-vendors"])


@router.post("/credit-check")
def credit_check():
    return {"status": "success", "score": 720, "vendor": "mock-credit"}


@router.post("/kyc")
def kyc_check():
    return {"status": "success", "vendor": "mock-kyc"}


@router.post("/kyb")
def kyb_check():
    return {"status": "success", "vendor": "mock-kyb"}


@router.post("/business-prefill")
def business_prefill():
    return {
        "status": "success",
        "vendor": "mock-biz",
        "data": {"company_name": "Sample Co", "state": "MN"},
    }


@router.post("/bank-verification")
def bank_verification():
    return {"status": "success", "vendor": "mock-bank", "balance": 100000}

