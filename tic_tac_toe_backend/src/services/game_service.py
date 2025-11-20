from __future__ import annotations

from typing import List, Optional, Tuple

from src.domain import create_new_game, apply_move, ai_pick_move
from src.schemas import GameStateResponse
from src.storage.repository import Repository, to_game_state_response


class GameService:
    """Service layer to orchestrate Tic Tac Toe domain logic and storage."""

    def __init__(self, repo: Repository) -> None:
        """Initialize the service with a repository implementation."""
        self._repo = repo

    # PUBLIC_INTERFACE
    def start_game(self, mode: str, ai_difficulty: Optional[str], first_player: str) -> GameStateResponse:
        """Create a new game using domain logic and persist it.

        Args:
            mode: 'pvp' or 'ai'.
            ai_difficulty: 'easy' or 'hard' if mode is 'ai', else None.
            first_player: 'X' or 'O'.

        Returns:
            GameStateResponse: The created game's current state.
        """
        state = create_new_game(
            first_player=first_player,
            mode=mode,  # type: ignore[arg-type]
            ai_difficulty=ai_difficulty if mode == "ai" else None,  # type: ignore[arg-type]
        )
        stored = self._repo.create_game(state)
        return to_game_state_response(stored)

    # PUBLIC_INTERFACE
    def get_game_state(self, game_id: str) -> Optional[GameStateResponse]:
        """Fetch a game's current state by id.

        Args:
            game_id: Game identifier.

        Returns:
            Optional[GameStateResponse]: The game state if found.
        """
        state = self._repo.get_game(game_id)
        if state is None:
            return None
        return to_game_state_response(state)

    # PUBLIC_INTERFACE
    def make_move(self, game_id: str, row: int, col: int) -> GameStateResponse:
        """Apply a player move and persist the updated state.

        Args:
            game_id: Game identifier.
            row: 0-based row index.
            col: 0-based column index.

        Returns:
            GameStateResponse: Updated game state.

        Raises:
            KeyError: If the game is not found.
            ValueError: If the move is invalid or game not in progress.
        """
        state = self._repo.get_game(game_id)
        if state is None:
            raise KeyError(f"Game with id {game_id} not found")
        updated = apply_move(state, row=row, col=col)
        saved = self._repo.update_game(updated)
        return to_game_state_response(saved)

    # PUBLIC_INTERFACE
    def ai_move(self, game_id: str) -> Tuple[Optional[Tuple[int, int]], GameStateResponse]:
        """Have the AI pick and apply a move when applicable.

        Behavior:
        - If game doesn't exist: KeyError.
        - If game is not in 'ai' mode or no move available: returns (None, current_state).
        - Otherwise applies the selected move and returns ((row, col), updated_state).

        Args:
            game_id: Game identifier.

        Returns:
            Tuple[Optional[(row, col)], GameStateResponse]: The move chosen and the resulting state.
        """
        state = self._repo.get_game(game_id)
        if state is None:
            raise KeyError(f"Game with id {game_id} not found")

        if state.get("mode") != "ai":
            # Not an AI game, return current state unchanged
            return None, to_game_state_response(state)

        move = ai_pick_move(state, difficulty=state.get("ai_difficulty"))
        if move is None:
            return None, to_game_state_response(state)

        row, col = move
        updated = apply_move(state, row=row, col=col)
        saved = self._repo.update_game(updated)
        return (row, col), to_game_state_response(saved)

    # PUBLIC_INTERFACE
    def list_games(self, offset: int = 0, limit: int = 50) -> List[GameStateResponse]:
        """List games using repository pagination and serialize to API model.

        Args:
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            List[GameStateResponse]: Page of games as API models.
        """
        games = self._repo.list_games(offset=offset, limit=limit)
        return [to_game_state_response(g) for g in games]
