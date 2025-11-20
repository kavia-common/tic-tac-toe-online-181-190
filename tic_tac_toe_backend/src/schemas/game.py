from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


Mode = Literal["pvp", "ai"]
Difficulty = Literal["easy", "hard"]
Player = Literal["X", "O"]
Status = Literal["in_progress", "x_won", "o_won", "draw"]


# PUBLIC_INTERFACE
class GameCreateRequest(BaseModel):
    """Request body to create a new game."""
    mode: Mode = Field(..., description="Game mode: 'pvp' for player vs player, 'ai' for playing against computer.")
    ai_difficulty: Difficulty = Field("easy", description="AI difficulty if mode is 'ai'. Defaults to 'easy'.")
    first_player: Player = Field("X", description="Player who starts the game, 'X' or 'O'.")


# PUBLIC_INTERFACE
class MoveRequest(BaseModel):
    """Request body to apply a move on the board."""
    row: int = Field(..., description="0-based row index.")
    col: int = Field(..., description="0-based column index.")


# PUBLIC_INTERFACE
class GameStateResponse(BaseModel):
    """Response model representing the current game state.

    Notes:
      - Board cells use None in the API for empty spaces (internal model uses empty string '').
    """
    id: str = Field(..., description="Unique game identifier.")
    board: List[List[Optional[str]]] = Field(..., description="3x3 board. 'X', 'O', or null for empty.")
    next_player: Optional[Player] = Field(None, description="Next player to move or null if game ended.")
    status: Status = Field(..., description="Game status.")
    mode: Mode = Field(..., description="Game mode.")
    ai_difficulty: Optional[str] = Field(None, description="AI difficulty if mode is 'ai', else null.")
    first_player: Player = Field(..., description="Player who started the game.")
    moves: int = Field(..., description="Number of moves made so far.")
