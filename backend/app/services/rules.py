from typing import Any, Dict, List, Tuple

from app.models.lender import LenderCriteria


def coerce_value(data_type: str, value: Any):
    if value is None:
        return None
    if data_type in ("int", "integer"):
        return int(value)
    if data_type in ("decimal", "float", "number"):
        return float(value)
    if data_type == "bool":
        return bool(value)
    return str(value)


def evaluate_rule(feature_value: Any, crit: LenderCriteria) -> bool:
    dt = crit.data_type
    op = crit.operator
    val = coerce_value(dt, feature_value)

    if op == "range":
        lo = coerce_value(dt, crit.value_min) if crit.value_min is not None else None
        hi = coerce_value(dt, crit.value_max) if crit.value_max is not None else None
        if val is None:
            return False
        if lo is not None and val < lo:
            return False
        if hi is not None and val > hi:
            return False
        return True

    if op == "in":
        if crit.values is None:
            return False
        return val in [coerce_value(dt, v) for v in crit.values]

    if op == "not_in":
        if crit.values is None:
            return True
        return val not in [coerce_value(dt, v) for v in crit.values]

    if op == "contains":
        if val is None or crit.pattern is None:
            return False
        return str(crit.pattern).lower() in str(val).lower()

    if op == "boolean":
        if crit.value_min is None:
            return bool(val)
        return bool(val) == bool(coerce_value("bool", crit.value_min))

    return False


def evaluate_program(features: Dict[str, Any], criteria: List[LenderCriteria]) -> Tuple[bool, List[Dict[str, Any]]]:
    results = []
    eligible = True
    for crit in criteria:
        fv = features.get(crit.field_key)
        passed = evaluate_rule(fv, crit)
        results.append(
            {
                "field": crit.field_key,
                "operator": crit.operator,
                "data_type": crit.data_type,
                "value": fv,
                "description": crit.description,
                "passed": passed,
            }
        )
        if not passed:
            eligible = False
    return eligible, results

