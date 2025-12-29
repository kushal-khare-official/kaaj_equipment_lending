from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.application import Application, MatchResult, MatchRun
from app.models.lender import LenderProgram, LenderCriteria
from app.services.feature_derivation import derive_application_features
from app.services.rules import evaluate_program


def compute_fit_score(results: List[Dict[str, Any]], total_criteria: int) -> int:
    """
    Compute a fit score from 0-100 based on how many criteria passed.
    Score is weighted: more criteria passed = higher score.
    """
    if total_criteria == 0:
        return 100

    passed_count = sum(1 for r in results if r["passed"])
    # Base score from pass rate
    base_score = int((passed_count / total_criteria) * 100)
    return max(0, min(100, base_score))


def format_expected_value(crit: LenderCriteria) -> str:
    """Format the expected value for a criterion based on its operator."""
    op = crit.operator
    if op == "range":
        parts = []
        if crit.value_min is not None:
            parts.append(f">= {crit.value_min}")
        if crit.value_max is not None:
            parts.append(f"<= {crit.value_max}")
        return " and ".join(parts) if parts else "any"
    elif op == "in":
        return f"one of: {', '.join(str(v) for v in (crit.values or []))}"
    elif op == "not_in":
        return f"not in: {', '.join(str(v) for v in (crit.values or []))}"
    elif op == "contains":
        return f"contains '{crit.pattern}'"
    elif op == "boolean":
        expected = crit.value_min if crit.value_min is not None else "true"
        return str(expected).lower()
    return "unknown"


def evaluate_application_against_program(
    app: Application, program: LenderProgram
) -> Tuple[bool, int, str, List[Dict[str, Any]]]:
    """
    Evaluate an application against a lender program.

    Returns:
        - eligible: bool - whether all criteria passed
        - fit_score: int - 0-100 score
        - reasons: str - semicolon-separated list of failed criteria
        - per_rule: list - detailed results for each criterion
    """
    features = derive_application_features(app)
    eligible, per_rule = evaluate_program(features, program.criteria)

    # Enrich per_rule with expected values
    enriched_results = []
    for i, r in enumerate(per_rule):
        crit = program.criteria[i]
        enriched_results.append({
            **r,
            "expected": format_expected_value(crit),
            "value": str(r.get("value")) if r.get("value") is not None else None,
        })

    fit_score = compute_fit_score(enriched_results, len(program.criteria))

    # Build reasons string from failed criteria
    failed_reasons = []
    for r in enriched_results:
        if not r["passed"]:
            desc = r.get("description") or r["field"]
            actual = r.get("value", "N/A")
            expected = r.get("expected", "")
            failed_reasons.append(f"{desc} (got: {actual}, expected: {expected})")

    reasons = "; ".join(failed_reasons)

    return eligible, fit_score, reasons, enriched_results


def calculate_assigned_term(program: LenderProgram, app: Application) -> Optional[int]:
    """
    Calculate the assigned loan term based on the program configuration and equipment.

    Logic:
    - If equipment is older (year < current_year - 5) or has high mileage (> 100k), use term_used_equipment
    - Otherwise use term_default
    - Clamp result between term_min and term_max
    """
    if not program.term_default:
        return None

    current_year = datetime.now().year
    is_used_equipment = False

    # Check if equipment qualifies as "used"
    if app.equipment:
        for eq in app.equipment:
            # Equipment older than 5 years
            if eq.year and eq.year < (current_year - 5):
                is_used_equipment = True
                break
            # High mileage (over 100k)
            if eq.mileage and eq.mileage > 100000:
                is_used_equipment = True
                break

    # Determine base term
    if is_used_equipment and program.term_used_equipment:
        base_term = program.term_used_equipment
    else:
        base_term = program.term_default

    # Clamp to min/max
    if program.term_min and base_term < program.term_min:
        base_term = program.term_min
    if program.term_max and base_term > program.term_max:
        base_term = program.term_max

    return base_term


def calculate_interest_rate(program: LenderProgram, app: Application, fit_score: int) -> Optional[float]:
    """
    Calculate the assigned interest rate based on the program configuration and fit score.

    Logic:
    - Base rate is the default rate
    - Higher fit scores get rates closer to minimum
    - Lower fit scores get rates closer to maximum
    """
    if not program.interest_rate_default:
        return None

    default_rate = float(program.interest_rate_default)
    min_rate = float(program.interest_rate_min) if program.interest_rate_min else default_rate
    max_rate = float(program.interest_rate_max) if program.interest_rate_max else default_rate

    # Calculate rate based on fit score (0-100)
    # Higher fit score = lower rate (better for borrower)
    if fit_score >= 90:
        return min_rate
    elif fit_score >= 80:
        # Interpolate between min and default
        ratio = (fit_score - 80) / 10
        return round(default_rate - (default_rate - min_rate) * ratio, 2)
    elif fit_score >= 70:
        return default_rate
    else:
        # Interpolate between default and max
        ratio = max(0, (70 - fit_score)) / 70
        return round(min(max_rate, default_rate + (max_rate - default_rate) * ratio), 2)


def get_program_match_summary(program: LenderProgram, eligible: bool, fit_score: int, app: Application = None) -> Dict[str, Any]:
    """Get a summary of the match result for a program."""
    summary = {
        "program_id": str(program.id),
        "program_name": program.name,
        "lender_id": str(program.lender_id),
        "lender_name": program.lender.name if program.lender else None,
        "eligible": eligible,
        "fit_score": fit_score,
    }

    # If eligible, calculate and include the assigned term
    if eligible and app:
        assigned_term = calculate_assigned_term(program, app)
        if assigned_term:
            summary["assigned_term_months"] = assigned_term

    return summary
