"""
Hatchet-like workflow stub: validate -> feature derivation -> parallel lender eval -> aggregate.
"""
from typing import Dict, List

from app.models.application import Application, MatchRun, MatchResult
from app.models.lender import LenderProgram
from app.services.matching import evaluate_application_against_program
from app.services.feature_derivation import derive_application_features


def run_match_workflow(app: Application, programs: List[LenderProgram]):
    features = derive_application_features(app)
    run = MatchRun(application_id=app.id, status="completed")
    results: List[MatchResult] = []
    for program in programs:
        eligible, fit_score, reasons, per_rule = evaluate_application_against_program(app, program)
        result = MatchResult(
            match_run_id=run.id,
            lender_program_id=program.id,
            eligible=eligible,
            fit_score=fit_score,
            reasons=reasons,
            criterion_results=per_rule,
        )
        results.append(result)
    run.results = results
    return run

