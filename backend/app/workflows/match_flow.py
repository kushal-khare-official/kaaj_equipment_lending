"""
Hatchet-like workflow stub: validate -> feature derivation -> parallel lender eval -> aggregate.
"""
from typing import Dict, List

from app.models.application import Application, MatchRun, MatchResult
from app.models.lender import LenderProgram
from app.services.matching import evaluate_application_against_program, calculate_assigned_term, calculate_interest_rate
from app.services.feature_derivation import derive_application_features


def run_match_workflow(app: Application, programs: List[LenderProgram], check_results: Dict | None = None):
    """
    Run the matching workflow for an application against all lender programs.

    Args:
        app: The application to evaluate
        programs: List of lender programs to match against
        check_results: Optional dict of external check results (credit, kyc, kyb, etc.)

    Returns:
        MatchRun with results for each program
    """
    features = derive_application_features(app)
    run = MatchRun(application_id=app.id, status="completed", check_results=check_results or {})
    results: List[MatchResult] = []

    for program in programs:
        eligible, fit_score, reasons, per_rule = evaluate_application_against_program(app, program)

        # Get lender name from the program's relationship
        lender_name = program.lender.name if program.lender else None

        # Calculate assigned term and interest rate if eligible
        assigned_term = None
        assigned_interest_rate = None
        if eligible:
            assigned_term = calculate_assigned_term(program, app)
            assigned_interest_rate = calculate_interest_rate(program, app, fit_score)

        result = MatchResult(
            lender_program_id=program.id,
            eligible=eligible,
            fit_score=fit_score,
            reasons=reasons,
            criterion_results={
                "lender_name": lender_name,
                "program_name": program.name,
                "criteria": per_rule,
                "assigned_term_months": assigned_term,
                "assigned_interest_rate": assigned_interest_rate,
            },
        )
        results.append(result)

    # Sort results: eligible first, then by fit_score descending
    results.sort(key=lambda r: (not r.eligible, -(r.fit_score or 0)))

    # Assign results via relationship - SQLAlchemy will handle match_run_id
    run.results = results
    return run
