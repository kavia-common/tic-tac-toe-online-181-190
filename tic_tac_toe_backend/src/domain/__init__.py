"""Domain package for Tic Tac Toe game logic.

Exports pure functions for creating and updating game states, checking winners,
listing available moves, and selecting AI moves.
"""

from .game_logic import (
    create_new_game,
    apply_move,
    check_winner,
    available_moves,
    ai_pick_move,
)

__all__ = [
    "create_new_game",
    "apply_move",
    "check_winner",
    "available_moves",
    "ai_pick_move",
]
