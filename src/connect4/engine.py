"""Immutable bitboard game state, independent of any user interface."""

from dataclasses import dataclass
from typing import Protocol

ROWS, COLS = 6, 7


@dataclass(frozen=True, slots=True)
class Game:
    bits: tuple[int, int] = (0, 0)
    heights: tuple[int, ...] = (0,) * COLS
    turn: int = 0
    winner: int | None = None

    @property
    def terminal(self) -> bool:
        return self.winner is not None or sum(self.heights) == ROWS * COLS

    def legal_moves(self) -> tuple[int, ...]:
        if self.terminal:
            return ()
        return tuple(c for c in range(COLS) if self.heights[c] < ROWS)

    def play(self, column: int) -> "Game":
        if type(column) is not int or column not in self.legal_moves():
            raise ValueError("Choose an available column from 0 to 6.")
        boards = list(self.bits)
        boards[self.turn] |= 1 << (column * 7 + self.heights[column])
        heights = list(self.heights)
        heights[column] += 1
        b = boards[self.turn]
        won = any(
            (b & (b >> d) & (b >> (2 * d)) & (b >> (3 * d))) for d in (1, 7, 6, 8)
        )
        return Game(
            tuple(boards), tuple(heights), 1 - self.turn, self.turn if won else None
        )

    def board(self) -> list[list[int]]:
        return [
            [
                next((p + 1 for p in (0, 1) if self.bits[p] & (1 << (c * 7 + r))), 0)
                for c in range(COLS)
            ]
            for r in reversed(range(ROWS))
        ]


class Agent(Protocol):
    def choose(self, game: Game) -> int: ...


def simulate(first: Agent, second: Agent) -> Game:
    game = Game()
    agents = (first, second)
    while not game.terminal:
        game = game.play(agents[game.turn].choose(game))
    return game
