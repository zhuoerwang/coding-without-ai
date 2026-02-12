# Project 5: Checker Board Game

## Level 1: Board Representation + Move Generation

**Implement classes:**

```
class Piece:
    # Represents a checker piece

class Board:
    __init__() -> None                          # 8x8 board with standard starting positions
    get(row: int, col: int) -> Piece | None     # get piece at position
    display() -> str                            # text representation of the board
    get_valid_moves(row: int, col: int) -> list[tuple[int, int]]  # valid destination squares
```

**Requirements:**
- 8x8 board, pieces on dark squares only
- Two players: BLACK and RED
- Standard checkers starting position: 12 pieces per side, rows 0-2 (BLACK) and rows 5-7 (RED)
- Pieces can only move diagonally forward (1 step)
  - BLACK moves toward higher rows, RED moves toward lower rows
- `get_valid_moves` returns positions the piece can move to (empty diagonal squares)
- Board coordinates: (0,0) is top-left

**Test Cases:**
```python
board = Board()
# Starting position: 12 black pieces on rows 0-2, 12 red pieces on rows 5-7
assert board.get(0, 1) is not None  # black piece
assert board.get(0, 1).color == "BLACK"
assert board.get(7, 0) is not None  # red piece
assert board.get(3, 0) is None      # empty square

# Black piece at (2, 1) can move to (3, 0) and (3, 2)
moves = board.get_valid_moves(2, 1)
assert (3, 0) in moves
assert (3, 2) in moves
```

---

## Level 2: Game Engine

**Implement a class `Game`:**

```
__init__() -> None
move(from_row: int, from_col: int, to_row: int, to_col: int) -> bool  # returns True if valid
get_winner() -> str | None         # "BLACK", "RED", or None if game ongoing
current_turn() -> str              # "BLACK" or "RED"
get_valid_moves(row: int, col: int) -> list[tuple[int, int]]  # includes captures
```

**Requirements:**
- Turn-based: BLACK moves first, alternates
- Captures: jump over opponent piece diagonally to land on empty square behind it
  - Captured piece is removed from board
- Multi-jump: if after a capture another capture is available with the same piece, must continue jumping
- Forced capture: if a capture is available, player must take it
- King promotion: piece reaching opposite end becomes a king
  - Kings can move/capture diagonally in all 4 directions
- Win condition: opponent has no pieces OR no valid moves

**Test Cases:**
```python
game = Game()
assert game.current_turn() == "BLACK"
assert game.move(2, 1, 3, 0) is True    # valid black move
assert game.current_turn() == "RED"
assert game.move(2, 3, 3, 4) is False   # wrong turn (black piece)
assert game.get_winner() is None         # game still going
```

---

## Level 3: Minimax AI

**Add AI player:**

```
class CheckerAI:
    __init__(depth: int = 4)
    best_move(game: Game) -> tuple[int, int, int, int]  # (from_row, from_col, to_row, to_col)
```

**Requirements:**
- Minimax algorithm with depth limit
- Evaluation function considering:
  - Material count (piece difference)
  - Kings worth more than regular pieces
  - Positional advantage (center control, advancement)
- Returns the best move for the current player
- Handle multi-jump sequences as single moves

**Key concepts:**
- Recursively explore game tree
- Maximize score for current player, minimize for opponent
- Terminal conditions: win/loss/draw or depth limit reached
- Need efficient board copy for exploring branches

**Test Cases:**
```python
game = Game()
ai = CheckerAI(depth=4)
move = ai.best_move(game)
assert len(move) == 4  # (from_row, from_col, to_row, to_col)
fr, fc, tr, tc = move
assert game.move(fr, fc, tr, tc) is True  # AI returns a valid move
```

---

## Level 4: Alpha-Beta Pruning

**Modify `CheckerAI`:**

```
__init__(depth: int = 4, use_alpha_beta: bool = True)
```

**Requirements:**
- Alpha-beta pruning to skip branches that can't affect the result
- Same results as minimax but explores fewer nodes
- Move ordering heuristic: try captures first, then moves toward center
- Track nodes evaluated to verify pruning effectiveness

**Key concepts:**
- Alpha = best score maximizer can guarantee
- Beta = best score minimizer can guarantee
- Prune when alpha >= beta
- Move ordering dramatically improves pruning efficiency

**Test Cases:**
```python
ai_basic = CheckerAI(depth=6, use_alpha_beta=False)
ai_pruned = CheckerAI(depth=6, use_alpha_beta=True)

game = Game()
# Both should return the same (or equally good) move
move1 = ai_basic.best_move(game)
move2 = ai_pruned.best_move(game)

# Pruned version should evaluate fewer nodes
assert ai_pruned.nodes_evaluated < ai_basic.nodes_evaluated
```
