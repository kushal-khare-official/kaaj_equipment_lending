"""
Hatchet client initialization and configuration.

This module provides a singleton Hatchet client instance that can be
imported and used throughout the application.

Hatchet SDK v0.40+ compatible.
"""
import logging
from functools import lru_cache
from typing import Optional

from hatchet_sdk import Hatchet, ClientConfig

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_hatchet_client() -> Hatchet:
    """
    Get or create the Hatchet client singleton.
    
    Configures the client based on environment settings:
    - HATCHET_CLIENT_TOKEN: API token (required)
    - HATCHET_HOST_PORT: Server address (default: localhost:7070)
    - HATCHET_TLS_ENABLED: Enable TLS (default: false)
    
    Returns:
        Hatchet: Configured Hatchet client instance
    """
    # Use Hatchet.from_environment() which reads from env vars automatically
    # HATCHET_CLIENT_TOKEN is required by the SDK
    
    logger.info(
        f"Initializing Hatchet client: host={settings.hatchet_host_port}, "
        f"tls={settings.hatchet_tls_enabled}"
    )
    
    # The SDK reads HATCHET_CLIENT_TOKEN from environment automatically
    return Hatchet.from_environment()


def reset_hatchet_client() -> None:
    """
    Reset the cached Hatchet client.
    
    Useful for testing or when configuration changes.
    """
    get_hatchet_client.cache_clear()


# Singleton instance - import this in workflow modules
# Note: This will fail if HATCHET_CLIENT_TOKEN is not set
# For development without Hatchet, use the sync workflow functions directly
try:
    hatchet = get_hatchet_client()
except ValueError as e:
    logger.warning(f"Hatchet client not initialized: {e}. Workflows will run synchronously.")
    hatchet = None
