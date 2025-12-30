"""
Hatchet Worker Entry Point.

This module provides the worker setup for running Hatchet workflows.
Run this as a separate process to handle workflow executions.

Usage:
    python -m app.workflows.worker

Hatchet SDK v0.40+ compatible.
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Global worker instance for graceful shutdown
_worker: Optional[object] = None


def create_worker(name: str = "lender-matching-worker"):
    """
    Create and configure the Hatchet worker.

    Args:
        name: Worker name for identification in Hatchet dashboard

    Returns:
        Configured Hatchet worker instance
    """
    global _worker

    from app.workflows.hatchet_client import hatchet
    
    if hatchet is None:
        raise RuntimeError(
            "Hatchet client not initialized. "
            "Please set HATCHET_CLIENT_TOKEN environment variable."
        )

    logger.info(f"Creating Hatchet worker: {name}")

    worker = hatchet.worker(name)

    # Import workflows to register them
    from app.workflows.application_workflow import ApplicationWorkflow
    from app.workflows.match_flow import MatchWorkflow

    # Register all workflows - must pass instances, not classes
    worker.register_workflow(ApplicationWorkflow())
    worker.register_workflow(MatchWorkflow())

    logger.info("Registered workflows: ApplicationWorkflow, MatchWorkflow")

    _worker = worker
    return worker


def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if _worker:
        try:
            _worker.stop()
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")
    sys.exit(0)


def run_worker():
    """
    Run the Hatchet worker synchronously.

    This is the main entry point for running the worker as a standalone process.
    """
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    worker = create_worker()

    logger.info("Starting Hatchet worker...")
    logger.info("Press Ctrl+C to stop")

    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        logger.info("Worker stopped")


async def run_worker_async():
    """
    Run the Hatchet worker asynchronously.

    Use this when integrating with async frameworks like FastAPI.
    """
    worker = create_worker()

    logger.info("Starting Hatchet worker (async)...")

    try:
        await worker.async_start()
    except asyncio.CancelledError:
        logger.info("Worker cancelled")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        logger.info("Worker stopped")


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    run_worker()
