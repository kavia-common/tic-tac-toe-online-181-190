from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field

from src.api.errors import not_found, bad_request
from src.api.deps import repository_dependency
from src.domain import (
    create_new_game,
    apply_move,
    ai_pick_move,
)
from src.schemas import GameCreateRequest, MoveRequest, GameStateResponse
from src.storage.repository import Repository, to_game_state_response


router = APIRouter(
    prefix="/games",
    tags=["Games"],
)


class ListGamesResponse(BaseModel):
    """Response model for listing games."""
    items: List[GameStateResponse] = Field(..., description="Paginated list of games.")
    offset: int = Field(..., description="Offset used for this page.")
    limit: int = Field(..., description="Limit used for this page.")
    count: int = Field(..., description="Number of items in this page.")


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=GameStateResponse,
    summary="Create a new game",
    description="Start a new Tic Tac Toe game, optionally against an AI.",
    responses={
        201: {"description": "Game created"},
        400: {"description": "Invalid request"},
    },
    status_code=201,
)
def create_game(
    payload: GameCreateRequest,
    repo: Repository = Depends(repository_dependency),
) -> GameStateResponse:
    """Create a new game using the domain logic and persist it.

    Args:
        payload: GameCreateRequest containing mode, ai_difficulty, and first_player.
        repo: Repository dependency.

    Returns:
        GameStateResponse with the current game state.
    """
    state = create_new_game(
        first_player=payload.first_player,
        mode=payload.mode,
        ai_difficulty=payload.ai_difficulty if payload.mode == "ai" else None,
    )
    stored = repo.create_game(state)
    return to_game_state_response(stored)


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=ListGamesResponse,
    summary="List games",
    description="List existing games with pagination.",
    responses={200: {"description": "List of games"}},
)
def list_games(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    repo: Repository = Depends(repository_dependency),
) -> ListGamesResponse:
    """List games stored in the repository using simple pagination."""
    games = repo.list_games(offset=offset, limit=limit)
    items = [to_game_state_response(g) for g in games]
    return ListGamesResponse(items=items, offset=offset, limit=limit, count=len(items))


# PUBLIC_INTERFACE
@router.get(
    "/{game_id}",
    response_model=GameStateResponse,
    summary="Get game by id",
    description="Fetch a specific game's current state.",
    responses={
        200: {"description": "Game state"},
        404: {"description": "Game not found"},
    },
)
def get_game(
    game_id: str = Path(..., description="Game identifier"),
    repo: Repository = Depends(repository_dependency),
) -> GameStateResponse:
    """Retrieve a game state by its id."""
    state = repo.get_game(game_id)
    if state is None:
        raise not_found(f"Game with id {game_id} not found")
    return to_game_state_response(state)


# PUBLIC_INTERFACE
@router.post(
    "/{game_id}/moves",
    response_model=GameStateResponse,
    summary="Apply a player move",
    description="Apply a player move to the specified game.",
    responses={
        200: {"description": "Move applied"},
        400: {"description": "Invalid move or request"},
        404: {"description": "Game not found"},
    },
)
def post_move(
    game_id: str,
    payload: MoveRequest,
    repo: Repository = Depends(repository_dependency),
) -> GameStateResponse:
    """Apply a player move (row, col) to an existing game.

    Validates game existence and delegates rules to domain logic.
    """
    state = repo.get_game(game_id)
    if state is None:
        raise not_found(f"Game with id {game_id} not found")

    try:
        updated = apply_move(state, row=payload.row, col=payload.col)
    except ValueError as ve:
        raise bad_request(str(ve))

    saved = repo.update_game(updated)
    return to_game_state_response(saved)


class AiMoveResponse(BaseModel):
    """Response payload for AI move application."""
    move: Optional[tuple[int, int]] = Field(
        None, description="Move chosen by AI as (row, col) or null if none."
    )
    state: GameStateResponse = Field(..., description="Updated game state after AI move (if any).")


# PUBLIC_INTERFACE
@router.post(
    "/{game_id}/ai-move",
    response_model=AiMoveResponse,
    summary="Apply an AI move",
    description="Ask the AI to make a move for the current player when the game is in AI mode.",
    responses={
        200: {"description": "AI move applied (or none available)"},
        400: {"description": "Invalid state for AI or request"},
        404: {"description": "Game not found"},
    },
)
def post_ai_move(
    game_id: str,
    repo: Repository = Depends(repository_dependency),
) -> AiMoveResponse:
    """Have the AI select a move and apply it if possible.

    Returns the selected move and the updated game state. If no move is possible
    or the game is not in AI mode/in progress, 'move' will be null and the state unchanged.
    """
    state = repo.get_game(game_id)
    if state is None:
        raise not_found(f"Game with id {game_id} not found")

    if state.get("mode") != "ai":
        # Not an AI game, just return current state
        return AiMoveResponse(move=None, state=to_game_state_response(state))

    move = ai_pick_move(state, difficulty=state.get("ai_difficulty"))
    if move is None:
        # No move available or invalid state; return unchanged
        return AiMoveResponse(move=None, state=to_game_state_response(state))

    row, col = move
    try:
        updated = apply_move(state, row=row, col=col)
    except ValueError as ve:
        # Shouldn't generally happen because ai_pick_move returns valid moves,
        # but guard anyway.
        raise bad_request(str(ve))

    saved = repo.update_game(updated)
    return AiMoveResponse(move=(row, col), state=to_game_state_response(saved))
