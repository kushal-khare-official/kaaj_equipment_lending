from datetime import datetime
from typing import Any, Dict, Optional

from app.models.application import Application


def derive_equipment_features(equipment: list) -> Dict[str, Any]:
    features: Dict[str, Any] = {}
    now_year = datetime.utcnow().year
    for idx, eq in enumerate(equipment):
        prefix = f"equipment.{idx}"
        if eq.year:
            features[f"{prefix}.age_years"] = max(0, now_year - eq.year)
        if eq.mileage is not None:
            features[f"{prefix}.mileage"] = eq.mileage
        if eq.type:
            features[f"{prefix}.type"] = eq.type
        features[f"{prefix}.titled"] = bool(eq.titled)
        features[f"{prefix}.private_party"] = bool(eq.private_party)
    return features


def derive_application_features(app: Application) -> Dict[str, Any]:
    features: Dict[str, Any] = {
        "application.status": app.status.value if hasattr(app.status, "value") else str(app.status),
        "application.merchant_email": app.merchant_email,
    }
    if app.guarantors:
        primary = next((g for g in app.guarantors if g.is_primary), app.guarantors[0])
        if primary.fico is not None:
            features["guarantor.fico"] = primary.fico
        features["guarantor.cdl_flag"] = bool(primary.cdl_flag)
        features["guarantor.homeownership"] = bool(primary.homeownership) if primary.homeownership is not None else None
    if app.business_credit:
        if app.business_credit.paynet_score is not None:
            features["business.paynet_score"] = app.business_credit.paynet_score
        if app.business_credit.revolving_utilization is not None:
            features["business.revolving_utilization"] = app.business_credit.revolving_utilization
    if app.loan_request:
        if app.loan_request.amount is not None:
            features["loan.amount"] = float(app.loan_request.amount)
        if app.loan_request.term_months is not None:
            features["loan.term_months"] = app.loan_request.term_months
        if app.loan_request.down_payment is not None:
            features["loan.down_payment"] = float(app.loan_request.down_payment)
    if app.equipment:
        features.update(derive_equipment_features(app.equipment))
    return {k: v for k, v in features.items() if v is not None}

