from typing import Any, Dict, List

from app.models.application import Application, MatchResult, MatchRun
from app.models.lender import LenderProgram, LenderCriteria
from app.services.feature_derivation import derive_application_features
from app.services.rules import evaluate_program


def compute_fit_score(results: List[Dict[str, Any]]) -> int:
    score = 100
    for r in results:
        if not r["passed"]:
            score -= 20
    return max(0, min(100, score))


def evaluate_application_against_program(app: Application, program: LenderProgram):
    features = derive_application_features(app)
    eligible, per_rule = evaluate_program(features, program.criteria)
    fit_score = compute_fit_score(per_rule)
    reasons = "; ".join([r.get("description") or r["field"] for r in per_rule if not r["passed"]])
    return eligible, fit_score, reasons, per_rule

