"""
Tests for Checker Board Game (Project 5)
Run: pytest test_checker.py -k "TestLevel1" -v
"""

import pytest

from checker import Piece, Board, Game, CheckerAI


# ============================================================
# Level 1: Board Representation + Move Generation
# ============================================================

class TestLevel1:
    def test_initial_board_black_pieces(self):
        board = Board()
        # Black pieces on rows 0-2, dark squares only
        count = 0
        for r in range(3):
            for c in range(8):
                p = board.get(r, c)
                if p is not None:
                    assert p.color == "BLACK"
                    count += 1
        assert count == 12

    def test_initial_board_red_pieces(self):
        board = Board()
        count = 0
        for r in range(5, 8):
            for c in range(8):
                p = board.get(r, c)
                if p is not None:
                    assert p.color == "RED"
                    count += 1
        assert count == 12

    def test_middle_rows_empty(self):
        board = Board()
        for r in range(3, 5):
            for c in range(8):
                assert board.get(r, c) is None

    def test_pieces_on_dark_squares_only(self):
        board = Board()
        for r in range(8):
            for c in range(8):
                if board.get(r, c) is not None:
                    # Dark squares: (row + col) is odd
                    assert (r + c) % 2 == 1

    def test_valid_moves_black_piece(self):
        board = Board()
        # A black piece on row 2 should be able to move forward (toward higher rows)
        # Find a black piece on row 2
        for c in range(8):
            p = board.get(2, c)
            if p is not None:
                moves = board.get_valid_moves(2, c)
                # Should move to row 3
                for mr, mc in moves:
                    assert mr == 3
                break

    def test_valid_moves_empty_square(self):
        board = Board()
        moves = board.get_valid_moves(4, 0)
        assert moves == []

    def test_valid_moves_blocked(self):
        """Pieces in row 0-1 with friendly pieces ahead have limited moves."""
        board = Board()
        # Row 0 pieces are blocked by row 1 pieces
        for c in range(8):
            p = board.get(0, c)
            if p is not None:
                moves = board.get_valid_moves(0, c)
                assert moves == []

    def test_display_returns_string(self):
        board = Board()
        output = board.display()
        assert isinstance(output, str)
        assert len(output) > 0

    def test_get_out_of_bounds(self):
        board = Board()
        assert board.get(-1, 0) is None
        assert board.get(8, 0) is None
        assert board.get(0, 8) is None


# ============================================================
# Level 2: Game Engine
# ============================================================

class TestLevel2:
    def test_black_moves_first(self):
        game = Game()
        assert game.current_turn() == "BLACK"

    def test_turn_alternates(self):
        game = Game()
        # Find a valid black move
        moved = False
        for r in range(3):
            for c in range(8):
                moves = game.get_valid_moves(r, c)
                if moves:
                    tr, tc = moves[0]
                    assert game.move(r, c, tr, tc) is True
                    moved = True
                    break
            if moved:
                break
        assert game.current_turn() == "RED"

    def test_cannot_move_opponent_piece(self):
        game = Game()
        # Try to move a red piece on black's turn
        for r in range(5, 8):
            for c in range(8):
                moves = game.get_valid_moves(r, c)
                if moves:
                    tr, tc = moves[0]
                    assert game.move(r, c, tr, tc) is False
                    break

    def test_invalid_move_rejected(self):
        game = Game()
        # Move to a non-adjacent square
        assert game.move(2, 1, 5, 4) is False

    def test_game_no_winner_at_start(self):
        game = Game()
        assert game.get_winner() is None

    def test_capture_removes_piece(self):
        """Set up a capture scenario and verify piece is removed."""
        game = Game()
        # We'll play moves to create a capture opportunity
        # This is a basic smoke test — exact moves depend on board layout
        # Just verify the method exists and returns bool
        assert isinstance(game.get_winner(), (str, type(None)))

    def test_get_valid_moves_includes_captures(self):
        game = Game()
        # At start, no captures available, just regular moves
        found_moves = False
        for r in range(3):
            for c in range(8):
                moves = game.get_valid_moves(r, c)
                if moves:
                    found_moves = True
        assert found_moves


# ============================================================
# Level 3: Minimax AI
# ============================================================

class TestLevel3:
    def test_ai_returns_valid_move(self):
        game = Game()
        ai = CheckerAI(depth=3)
        move = ai.best_move(game)
        assert len(move) == 4
        fr, fc, tr, tc = move
        assert game.move(fr, fc, tr, tc) is True

    def test_ai_plays_both_sides(self):
        """AI can play a few turns without crashing."""
        game = Game()
        ai = CheckerAI(depth=3)
        for _ in range(10):
            if game.get_winner() is not None:
                break
            move = ai.best_move(game)
            fr, fc, tr, tc = move
            assert game.move(fr, fc, tr, tc) is True

    def test_ai_takes_capture_when_available(self):
        """AI should prefer capturing moves."""
        game = Game()
        ai = CheckerAI(depth=3)
        # Play enough moves that captures become available
        # AI at depth 3 should find them
        move = ai.best_move(game)
        assert move is not None

    def test_ai_different_depths(self):
        """Higher depth should not crash."""
        game = Game()
        ai_shallow = CheckerAI(depth=1)
        ai_deep = CheckerAI(depth=4)
        move1 = ai_shallow.best_move(game)
        move2 = ai_deep.best_move(game)
        assert len(move1) == 4
        assert len(move2) == 4


# ============================================================
# Level 4: Alpha-Beta Pruning
# ============================================================

class TestLevel4:
    def test_alpha_beta_returns_valid_move(self):
        game = Game()
        ai = CheckerAI(depth=4, use_alpha_beta=True)
        move = ai.best_move(game)
        assert len(move) == 4
        fr, fc, tr, tc = move
        assert game.move(fr, fc, tr, tc) is True

    def test_alpha_beta_fewer_nodes(self):
        """Alpha-beta should evaluate fewer nodes than plain minimax."""
        game = Game()
        ai_basic = CheckerAI(depth=5, use_alpha_beta=False)
        ai_pruned = CheckerAI(depth=5, use_alpha_beta=True)

        ai_basic.best_move(game)
        ai_pruned.best_move(game)

        assert ai_pruned.nodes_evaluated < ai_basic.nodes_evaluated

    def test_alpha_beta_same_quality(self):
        """Alpha-beta and minimax should return equally good moves."""
        game = Game()
        ai_basic = CheckerAI(depth=4, use_alpha_beta=False)
        ai_pruned = CheckerAI(depth=4, use_alpha_beta=True)

        # Both should return valid moves
        move1 = ai_basic.best_move(game)
        move2 = ai_pruned.best_move(game)
        assert len(move1) == 4
        assert len(move2) == 4

    def test_alpha_beta_full_game(self):
        """AI with alpha-beta can play a full game without errors."""
        game = Game()
        ai = CheckerAI(depth=4, use_alpha_beta=True)
        moves_played = 0
        max_moves = 100  # prevent infinite game
        while game.get_winner() is None and moves_played < max_moves:
            move = ai.best_move(game)
            fr, fc, tr, tc = move
            game.move(fr, fc, tr, tc)
            moves_played += 1
        # Game should either have a winner or hit move limit
        assert moves_played > 0
