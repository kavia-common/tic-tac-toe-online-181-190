from __future__ import annotations

from typing import Generator

from fastapi import Depends

from src.config import get_repository
from src.storage.repository import Repository


# PUBLIC_INTERFACE
def get_repo() -> Generator[Repository, None, None]:
    """Yield a Repository instance from configuration.

    Uses environment variables handled by src.config.get_repository.
    """
    repo = get_repository()
    try:
        yield repo
    finally:
        # For future backends (DB connections) we could close here.
        pass


# PUBLIC_INTERFACE
def repository_dependency(repo: Repository = Depends(get_repo)) -> Repository:
    """Convenience dependency to inject a Repository into route handlers."""
    return repo
