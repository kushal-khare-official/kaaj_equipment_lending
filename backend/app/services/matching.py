from typing import Any, Dict, List, Tuple

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


def get_program_match_summary(program: LenderProgram, eligible: bool, fit_score: int) -> Dict[str, Any]:
    """Get a summary of the match result for a program."""
    return {
        "program_id": str(program.id),
        "program_name": program.name,
        "lender_id": str(program.lender_id),
        "lender_name": program.lender.name if program.lender else None,
        "eligible": eligible,
        "fit_score": fit_score,
    }
