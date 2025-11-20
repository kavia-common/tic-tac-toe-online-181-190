from __future__ import annotations

import os
from typing import Optional

from src.storage.repository import InMemoryRepository, Repository


def _get_env_int(name: str) -> Optional[int]:
    """Fetch an integer env var if present; return None if missing or invalid."""
    val = os.getenv(name)
    if val is None or val == "":
        return None
    try:
        return int(val)
    except ValueError:
        return None


# PUBLIC_INTERFACE
def get_repository() -> Repository:
    """Return the configured Repository implementation.

    Environment variables:
    - STORE_BACKEND: select storage backend. Supported: 'in_memory' (default).
    - GAME_TTL_MINUTES: optional integer to set in-memory TTL for games.

    Returns:
        An instance implementing Repository.
    """
    backend = os.getenv("STORE_BACKEND", "in_memory").strip().lower()
    ttl_minutes = _get_env_int("GAME_TTL_MINUTES")

    if backend in ("in_memory", "memory", "mem"):
        return InMemoryRepository(game_ttl_minutes=ttl_minutes)

    # Fallback to in-memory if an unknown backend is provided to avoid crashing.
    return InMemoryRepository(game_ttl_minutes=ttl_minutes)
