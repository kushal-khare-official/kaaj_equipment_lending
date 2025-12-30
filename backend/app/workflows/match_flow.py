"""
Hatchet Workflow for Lender Matching.

A focused workflow that handles lender program matching for applications.
Can be run standalone or as part of the main application workflow.

Hatchet SDK v0.40+ compatible.
"""
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID

from hatchet_sdk import Context, workflow, step

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.application import Application, MatchRun, MatchResult
from app.models.lender import LenderProgram
from app.services.matching import (
    evaluate_application_against_program,
    calculate_assigned_term,
    calculate_interest_rate,
)
from app.services.feature_derivation import derive_application_features

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def get_db_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def load_application(db: Session, application_id: UUID) -> Optional[Application]:
    """Load application with all relationships."""
    return db.query(Application).filter(Application.id == application_id).first()


# =============================================================================
# Hatchet Workflow Definition
# =============================================================================

@workflow(name="match-workflow", on_events=["match:run"])
class MatchWorkflow:
    """
    Workflow for matching applications against lender programs.

    This workflow:
    1. Derives features from application data
    2. Evaluates each lender program's criteria
    3. Aggregates and sorts match results

    DAG Structure:
        derive_features → evaluate_programs → aggregate
    """

    # =========================================================================
    # Step 1: Derive Features
    # =========================================================================
    @step(timeout="10s", retries=1)
    async def derive_features(self, context: Context) -> Dict[str, Any]:
        """
        Derive normalized features from application data.

        Features are used for program evaluation and scoring.

        Returns:
            dict with application_id and features
        """
        input_data = context.workflow_input()
        application_id = UUID(input_data["application_id"])
        check_results = input_data.get("check_results", {})

        logger.info(f"[derive_features] Application {application_id}")

        db = get_db_session()
        try:
            application = load_application(db, application_id)
            if not application:
                return {
                    "application_id": str(application_id),
                    "features": {},
                    "error": f"Application {application_id} not found",
                }

            features = derive_application_features(application)

            logger.info(f"[derive_features] Derived {len(features)} features")

            return {
                "application_id": str(application_id),
                "features": features,
                "check_results": check_results,
            }

        finally:
            db.close()

    # =========================================================================
    # Step 2: Evaluate Programs
    # =========================================================================
    @step(timeout="30s", retries=2, parents=["derive_features"])
    async def evaluate_programs(self, context: Context) -> Dict[str, Any]:
        """
        Evaluate application against all active lender programs.

        Returns:
            dict with application_id and program_results list
        """
        derive_output = context.step_output("derive_features")

        application_id = UUID(derive_output["application_id"])

        if derive_output.get("error"):
            return {
                "application_id": str(application_id),
                "program_results": [],
                "error": derive_output["error"],
            }

        logger.info(f"[evaluate_programs] Application {application_id}")

        results = []
        db = get_db_session()
        try:
            application = load_application(db, application_id)
            if not application:
                return {
                    "application_id": str(application_id),
                    "program_results": [],
                    "error": f"Application {application_id} not found",
                }

            # Get active programs
            programs = db.query(LenderProgram).all()

            for program in programs:
                try:
                    eligible, fit_score, reasons, per_rule = evaluate_application_against_program(
                        application, program
                    )

                    lender_name = program.lender.name if program.lender else None

                    # Calculate terms for eligible programs
                    assigned_term = None
                    assigned_interest_rate = None
                    if eligible:
                        assigned_term = calculate_assigned_term(program, application)
                        assigned_interest_rate = calculate_interest_rate(program, application, fit_score)

                    results.append({
                        "lender_program_id": str(program.id),
                        "lender_name": lender_name,
                        "program_name": program.name,
                        "eligible": eligible,
                        "fit_score": fit_score,
                        "reasons": reasons,
                        "criterion_results": per_rule,
                        "assigned_term_months": assigned_term,
                        "assigned_interest_rate": assigned_interest_rate,
                    })

                except Exception as e:
                    logger.error(f"[evaluate_programs] Program {program.id} error: {str(e)}")
                    results.append({
                        "lender_program_id": str(program.id),
                        "lender_name": program.lender.name if program.lender else None,
                        "program_name": program.name,
                        "eligible": False,
                        "fit_score": 0,
                        "reasons": f"Evaluation error: {str(e)}",
                        "criterion_results": [],
                    })

            logger.info(f"[evaluate_programs] Evaluated {len(results)} programs")

            return {
                "application_id": str(application_id),
                "program_results": results,
            }

        finally:
            db.close()

    # =========================================================================
    # Step 3: Aggregate Results
    # =========================================================================
    @step(timeout="5s", retries=0, parents=["evaluate_programs"])
    async def aggregate(self, context: Context) -> Dict[str, Any]:
        """
        Sort and aggregate match results.

        Creates a MatchRun record with all results.

        Returns:
            dict with match_run_id, sorted results, and best program info
        """
        derive_output = context.step_output("derive_features")
        eval_output = context.step_output("evaluate_programs")

        application_id = UUID(eval_output["application_id"])
        check_results = derive_output.get("check_results", {})
        results = eval_output.get("program_results", [])

        if eval_output.get("error"):
            return {
                "match_run_id": None,
                "results": [],
                "best_lender_program_id": None,
                "best_term_months": None,
                "best_interest_rate": None,
                "error": eval_output["error"],
            }

        logger.info(f"[aggregate] Application {application_id}")

        # Sort results: eligible first, then by fit_score descending
        results.sort(key=lambda r: (not r["eligible"], -(r.get("fit_score") or 0)))

        # Find best program
        best_lender_program_id = None
        best_term_months = None
        best_interest_rate = None

        eligible_results = [r for r in results if r.get("eligible")]
        if eligible_results:
            sorted_eligible = sorted(
                eligible_results,
                key=lambda r: (
                    r.get("fit_score") or 0,
                    r.get("assigned_term_months") or 0,
                    -(r.get("assigned_interest_rate") or 100),
                ),
                reverse=True
            )

            best_program = sorted_eligible[0]
            best_lender_program_id = best_program.get("lender_program_id")
            best_term_months = best_program.get("assigned_term_months")
            best_interest_rate = best_program.get("assigned_interest_rate")

            logger.info(
                f"[aggregate] Best: {best_program.get('lender_name')} - {best_program.get('program_name')} "
                f"({best_term_months}mo @ {best_interest_rate}%)"
            )

        # Persist MatchRun
        db = get_db_session()
        try:
            match_run = MatchRun(
                application_id=application_id,
                status="completed",
                check_results=check_results,
            )

            for result in results:
                match_result = MatchResult(
                    lender_program_id=UUID(result["lender_program_id"]),
                    eligible=result["eligible"],
                    fit_score=result.get("fit_score"),
                    reasons=result.get("reasons"),
                    criterion_results={
                        "lender_name": result.get("lender_name"),
                        "program_name": result.get("program_name"),
                        "criteria": result.get("criterion_results", []),
                        "assigned_term_months": result.get("assigned_term_months"),
                        "assigned_interest_rate": result.get("assigned_interest_rate"),
                    },
                )
                match_run.results.append(match_result)

            db.add(match_run)
            db.commit()
            db.refresh(match_run)

            eligible_count = sum(1 for r in results if r["eligible"])
            logger.info(f"[aggregate] Complete: {eligible_count}/{len(results)} eligible, match_run_id={match_run.id}")

            return {
                "match_run_id": str(match_run.id),
                "results": results,
                "eligible_count": eligible_count,
                "total_count": len(results),
                "best_lender_program_id": best_lender_program_id,
                "best_term_months": best_term_months,
                "best_interest_rate": best_interest_rate,
            }

        finally:
            db.close()


# =============================================================================
# Convenience Functions
# =============================================================================

async def run_match_workflow_async(
    application_id: UUID,
    check_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the match workflow asynchronously via Hatchet.

    Args:
        application_id: The application to match
        check_results: Optional dict of external check results

    Returns:
        dict with match results
    """
    from app.workflows.hatchet_client import hatchet
    
    if hatchet is None:
        logger.warning("Hatchet not configured, cannot run async workflow")
        return {"error": "Hatchet not configured"}
    
    logger.info(f"Starting Hatchet match workflow for application {application_id}")

    workflow_input = {
        "application_id": str(application_id),
        "check_results": check_results or {},
    }

    workflow_ref = hatchet.admin.run_workflow(
        "match-workflow",
        workflow_input,
    )
    
    result = await workflow_ref.result()
    
    logger.info(f"Hatchet match workflow completed for application {application_id}")
    return result


def run_match_workflow(
    app: Application,
    programs: List[LenderProgram],
    check_results: Optional[Dict[str, Any]] = None,
) -> MatchRun:
    """
    Run the matching workflow for an application against all lender programs.

    This is a synchronous wrapper that maintains backward compatibility
    with the original function signature.

    Args:
        app: The application to evaluate
        programs: List of lender programs (not used, workflow queries active programs)
        check_results: Optional dict of external check results (credit, kyc, kyb, etc.)

    Returns:
        MatchRun with results for each program
    """
    logger.info(f"Running match workflow for application {app.id}")

    # For backward compatibility, run synchronously
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
