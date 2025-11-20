"""
Core Tic Tac Toe domain logic.

This module contains pure functions to create and update game state, validate moves,
determine winners or draw, compute next player, and provide a simple AI move picker.

Internal representation:
- Board is a 3x3 list of lists with values 'X', 'O', or '' for empty.
- Game state is a dict with:
    {
        'id': str,
        'board': list[list[str]],  # 3x3, 'X'|'O'|''
        'next_player': 'X'|'O'|None,
        'status': 'in_progress'|'x_won'|'o_won'|'draw',
        'mode': 'pvp'|'ai',
        'ai_difficulty': 'easy'|'hard'|None,
        'first_player': 'X'|'O',
        'moves': int
    }

Public interfaces return new structures instead of mutating inputs to be immutability-friendly.
"""

from __future__ import annotations

import random
import uuid
from copy import deepcopy
from typing import List, Optional, Tuple, Literal, Dict, Any

Player = Literal["X", "O"]
Cell = Literal["X", "O", ""]
Status = Literal["in_progress", "x_won", "o_won", "draw"]
Mode = Literal["pvp", "ai"]
Difficulty = Literal["easy", "hard"]


def _empty_board() -> List[List[Cell]]:
    """Return a new empty 3x3 board with '' cells."""
    return [["", "", ""], ["", "", ""], ["", "", ""]]


def _next_player_after(current: Optional[Player]) -> Optional[Player]:
    """Return the next player given current player. If None, return None."""
    if current is None:
        return None
    return "O" if current == "X" else "X"


# PUBLIC_INTERFACE
def create_new_game(first_player: Player, mode: Mode, ai_difficulty: Optional[Difficulty] = "easy") -> Dict[str, Any]:
    """Create a new game state.

    Args:
        first_player: 'X' or 'O' who starts the game.
        mode: 'pvp' or 'ai'
        ai_difficulty: 'easy' or 'hard' if mode is 'ai'; ignored otherwise. Defaults to 'easy'.

    Returns:
        A new game state dictionary.
    """
    game_id = str(uuid.uuid4())
    state = {
        "id": game_id,
        "board": _empty_board(),
        "next_player": first_player,
        "status": "in_progress",
        "mode": mode,
        "ai_difficulty": ai_difficulty if mode == "ai" else None,
        "first_player": first_player,
        "moves": 0,
    }
    return state


# PUBLIC_INTERFACE
def available_moves(board: List[List[Cell]]) -> List[Tuple[int, int]]:
    """Return a list of available moves (row, col) for the given board."""
    moves: List[Tuple[int, int]] = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == "":
                moves.append((r, c))
    return moves


def _lines(board: List[List[Cell]]) -> List[List[Cell]]:
    """Return all 8 lines (3 rows, 3 cols, 2 diagonals) as lists of 3 cells."""
    rows = board
    cols = [[board[r][c] for r in range(3)] for c in range(3)]
    diags = [
        [board[0][0], board[1][1], board[2][2]],
        [board[0][2], board[1][1], board[2][0]],
    ]
    return rows + cols + diags


# PUBLIC_INTERFACE
def check_winner(board: List[List[Cell]]) -> Optional[Literal["X", "O", "draw"]]:
    """Check if there's a winner or a draw.

    Returns:
        'X' if X won,
        'O' if O won,
        'draw' if no empty cells and no winner,
        None if the game is still in progress.
    """
    for line in _lines(board):
        if line[0] != "" and line[0] == line[1] == line[2]:
            return line[0]  # 'X' or 'O'
    if not available_moves(board):
        return "draw"
    return None


def _derive_status_from_winner(winner: Optional[Literal["X", "O", "draw"]]) -> Status:
    """Convert winner symbol to status string."""
    if winner == "X":
        return "x_won"
    if winner == "O":
        return "o_won"
    if winner == "draw":
        return "draw"
    return "in_progress"


# PUBLIC_INTERFACE
def apply_move(state: Dict[str, Any], row: int, col: int) -> Dict[str, Any]:
    """Apply a move to the game state and return a new updated state.

    Enforces:
      - Move is inside bounds.
      - Cell must be empty.
      - Game must be in progress.
      - Next player alternates deterministically.

    Args:
        state: Current game state dict.
        row: 0-based row index.
        col: 0-based col index.

    Returns:
        A new game state dict with the move applied or raises ValueError on invalid move.
    """
    if state.get("status") != "in_progress":
        raise ValueError("Game is not in progress.")

    if not (0 <= row < 3 and 0 <= col < 3):
        raise ValueError("Move out of bounds.")

    board = deepcopy(state["board"])
    current_player: Optional[Player] = state.get("next_player")
    if current_player is None:
        raise ValueError("No next player assigned.")

    if board[row][col] != "":
        raise ValueError("Cell already occupied.")

    # Place the mark
    board[row][col] = current_player

    # Evaluate winner/draw
    winner = check_winner(board)
    status = _derive_status_from_winner(winner)

    # Compute next player
    next_player: Optional[Player]
    if status == "in_progress":
        next_player = _next_player_after(current_player)
    else:
        next_player = None  # Game ended

    new_state = {
        **state,
        "board": board,
        "next_player": next_player,
        "status": status,
        "moves": int(state.get("moves", 0)) + 1,
    }
    return new_state


def _ai_easy_pick(moves: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """Pick a random move from the list (easy difficulty)."""
    if not moves:
        return None
    return random.choice(moves)


# Placeholder for potential future minimax-based hard AI
def _ai_hard_pick(state: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    """Future: implement minimax. For now, fallback to easy strategy."""
    return _ai_easy_pick(available_moves(state["board"]))


# PUBLIC_INTERFACE
def ai_pick_move(state: Dict[str, Any], difficulty: Optional[Difficulty] = "easy") -> Optional[Tuple[int, int]]:
    """Pick an AI move based on the difficulty.

    Args:
        state: current game state dict.
        difficulty: 'easy' or 'hard'. Defaults to 'easy'.

    Returns:
        (row, col) tuple for the selected move, or None if no moves available
        or if the game is not in a state where AI should move.
    """
    if state.get("status") != "in_progress":
        return None

    if state.get("mode") != "ai":
        return None

    # AI can play for whichever side is next_player.
    moves = available_moves(state["board"])
    if not moves:
        return None

    if difficulty == "hard":
        return _ai_hard_pick(state)
    return _ai_easy_pick(moves)
