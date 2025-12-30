"""
Hatchet Workflows for Lender Matching Platform.

This package contains workflow definitions using the Hatchet SDK v0.40+.

Workflows:
    - ApplicationWorkflow: Main application processing workflow with verification,
      document analysis, risk assessment, and lender matching.
    - MatchWorkflow: Standalone lender matching workflow.

Usage:
    # Import workflows
    from app.workflows import ApplicationWorkflow, MatchWorkflow

    # Import convenience functions
    from app.workflows import (
        run_application_workflow,
        run_workflow_sync,
        run_match_workflow,
    )

    # Import the Hatchet client (may be None if not configured)
    from app.workflows import hatchet

Worker:
    Run the worker to process workflows:
    
    ```bash
    # Set required environment variable
    export HATCHET_CLIENT_TOKEN=your-token
    
    # Run worker
    python -m app.workflows.worker
    ```

Note:
    If HATCHET_CLIENT_TOKEN is not set, workflows will run synchronously
    within the API server instead of via Hatchet.
"""

from app.workflows.hatchet_client import hatchet, get_hatchet_client, reset_hatchet_client

from app.workflows.application_workflow import (
    ApplicationWorkflow,
    run_application_workflow,
    run_workflow_sync,
)

from app.workflows.match_flow import (
    MatchWorkflow,
    run_match_workflow,
    run_match_workflow_async,
)

__all__ = [
    # Hatchet client (may be None)
    "hatchet",
    "get_hatchet_client",
    "reset_hatchet_client",
    # Application workflow
    "ApplicationWorkflow",
    "run_application_workflow",
    "run_workflow_sync",
    # Match workflow
    "MatchWorkflow",
    "run_match_workflow",
    "run_match_workflow_async",
]
