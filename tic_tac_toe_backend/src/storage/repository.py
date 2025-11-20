from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple

from src.schemas.game import GameStateResponse


@dataclass
class _StoredGame:
    """
    Internal stored representation of a game.

    We keep the raw state payload as a dict[str, any] so it remains compatible with
    the domain's data shape. A created_at timestamp allows future TTL cleanup.
    """
    state: Dict
    created_at: float = field(default_factory=lambda: time.time())


# PUBLIC_INTERFACE
class Repository(Protocol):
    """Abstract storage interface for game persistence."""

    # PUBLIC_INTERFACE
    def create_game(self, game: Dict) -> Dict:
        """Persist a new game and return the stored game state."""

    # PUBLIC_INTERFACE
    def get_game(self, game_id: str) -> Optional[Dict]:
        """Fetch a game by id, returning None if not found."""

    # PUBLIC_INTERFACE
    def update_game(self, game: Dict) -> Dict:
        """Update an existing game and return the updated state."""

    # PUBLIC_INTERFACE
    def list_games(self, offset: int = 0, limit: int = 50) -> List[Dict]:
        """List games with pagination."""


class InMemoryRepository:
    """
    Thread-safe in-memory repository using a dict for storage.

    Notes:
    - This is intended for development/testing.
    - Stores raw domain game dictionaries.
    - Simple optional TTL cleanup can be added via sweep_expired if TTL is provided.
    """

    def __init__(self, game_ttl_minutes: Optional[int] = None) -> None:
        self._lock = threading.Lock()
        self._games: Dict[str, _StoredGame] = {}
        self._ttl_seconds: Optional[int] = None
        if game_ttl_minutes and game_ttl_minutes > 0:
            self._ttl_seconds = int(game_ttl_minutes * 60)

    def _is_expired(self, stored: _StoredGame) -> bool:
        if self._ttl_seconds is None:
            return False
        return (time.time() - stored.created_at) > self._ttl_seconds

    def _get_if_present_and_not_expired(self, game_id: str) -> Optional[Dict]:
        stored = self._games.get(game_id)
        if stored is None:
            return None
        if self._is_expired(stored):
            # Clean up expired on access
            del self._games[game_id]
            return None
        return stored.state

    # PUBLIC_INTERFACE
    def create_game(self, game: Dict) -> Dict:
        """Persist a new game and return the stored game state."""
        game_id = str(game.get("id"))
        if not game_id:
            raise ValueError("Game must have an 'id' field.")
        with self._lock:
            if game_id in self._games:
                raise ValueError(f"Game with id {game_id} already exists.")
            self._games[game_id] = _StoredGame(state=game)
            return self._games[game_id].state

    # PUBLIC_INTERFACE
    def get_game(self, game_id: str) -> Optional[Dict]:
        """Fetch a game by id, returning None if not found."""
        with self._lock:
            return self._get_if_present_and_not_expired(game_id)

    # PUBLIC_INTERFACE
    def update_game(self, game: Dict) -> Dict:
        """Update an existing game and return the updated state."""
        game_id = str(game.get("id"))
        if not game_id:
            raise ValueError("Game must have an 'id' field.")
        with self._lock:
            if game_id not in self._games or self._is_expired(self._games[game_id]):
                raise KeyError(f"Game with id {game_id} not found.")
            self._games[game_id].state = game
            return self._games[game_id].state

    # PUBLIC_INTERFACE
    def list_games(self, offset: int = 0, limit: int = 50) -> List[Dict]:
        """List games with pagination."""
        with self._lock:
            # Remove expired first (lazy sweep)
            if self._ttl_seconds is not None:
                expired_ids: List[str] = []
                now = time.time()
                for gid, stored in self._games.items():
                    if (now - stored.created_at) > self._ttl_seconds:
                        expired_ids.append(gid)
                for gid in expired_ids:
                    del self._games[gid]

            # Return a stable ordering by created_at then id
            items: List[Tuple[str, _StoredGame]] = sorted(
                self._games.items(), key=lambda kv: (kv[1].created_at, kv[0])
            )
            page = items[offset : offset + limit]
            return [stored.state for _, stored in page]


# Helper to serialize internal dict to API schema when needed.
# PUBLIC_INTERFACE
def to_game_state_response(game: Dict) -> GameStateResponse:
    """Convert internal dict to GameStateResponse model.

    Converts board '' cells to None for API response.
    """
    board = game.get("board", [])
    api_board: List[List[Optional[str]]] = []
    for row in board:
        api_board.append([cell if cell != "" else None for cell in row])

    return GameStateResponse(
        id=str(game.get("id")),
        board=api_board,
        next_player=game.get("next_player"),
        status=game.get("status"),
        mode=game.get("mode"),
        ai_difficulty=game.get("ai_difficulty"),
        first_player=game.get("first_player"),
        moves=int(game.get("moves", 0)),
    )
