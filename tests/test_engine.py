import random

import pytest

from connect4.engine import Game


def position(moves):
    game = Game()
    for move in moves:
        game = game.play(move)
    return game


@pytest.mark.parametrize(
    "moves",
    [
        [0, 1, 0, 1, 0, 1, 0],
        [0, 0, 1, 1, 2, 2, 3],
        [0, 1, 1, 2, 4, 2, 2, 3, 4, 3, 5, 3, 3],
        [6, 5, 5, 4, 2, 4, 4, 3, 2, 3, 1, 3, 3],
    ],
)
def test_win_directions(moves):
    game = position(moves)
    assert game.winner == 0
    assert game.terminal
    assert not game.legal_moves()
    with pytest.raises(ValueError):
        game.play(0)


@pytest.mark.parametrize("move", [-1, 7, None, True, 1.5, "1"])
def test_invalid_move(move):
    with pytest.raises(ValueError):
        Game().play(move)


def test_gravity_and_immutability():
    game = Game()
    child = game.play(2).play(2)
    assert game.bits == (0, 0)
    assert child.board()[5][2] == 1
    assert child.board()[4][2] == 2
    full = position([0] * 6)
    with pytest.raises(ValueError):
        full.play(0)


def reference_winner(board):
    for r in range(6):
        for c in range(7):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [(r + i * dr, c + i * dc) for i in range(4)]
                if all(0 <= y < 6 and 0 <= x < 7 for y, x in cells):
                    values = [board[y][x] for y, x in cells]
                    if values[0] and len(set(values)) == 1:
                        return values[0] - 1
    return None


def test_random_games_against_independent_grid_oracle():
    rng = random.Random(54)
    draws = 0
    for _ in range(500):
        game = Game()
        while not game.terminal:
            game = game.play(rng.choice(game.legal_moves()))
            assert game.winner == reference_winner(game.board())
        draws += game.winner is None
        assert game.winner is not None or sum(game.heights) == 42
    assert draws > 0
