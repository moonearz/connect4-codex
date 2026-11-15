"""Small zero-sum TD(0) value model trained by epsilon-greedy self-play."""

import argparse
import json
import math
import random
import time
from pathlib import Path

from connect4.agents import WINDOWS
from connect4.engine import Game

DEFAULT_MODEL = Path(__file__).parent / "data" / "learner.json"


def features(game):
    own, other = game.bits[game.turn], game.bits[1 - game.turn]
    counts = [0.0] * 8
    for window in WINDOWS:
        a, b = (own & window).bit_count(), (other & window).bit_count()
        if a and not b and a < 4:
            counts[a - 1] += 0.125
        if b and not a and b < 4:
            counts[b + 2] += 0.125
    center = sum(1 << (3 * 7 + r) for r in range(6))
    counts[6] = ((own & center).bit_count() - (other & center).bit_count()) / 6
    counts[7] = 1.0
    return counts


class LearningAgent:
    def __init__(self, weights=None, seed=0):
        self.weights = list(weights) if weights is not None else [0.0] * 8
        if len(self.weights) != 8 or not all(math.isfinite(w) for w in self.weights):
            raise ValueError("Expected eight finite feature weights.")
        self.rng = random.Random(seed)

    def value(self, game):
        return math.tanh(
            sum(w * x for w, x in zip(self.weights, features(game), strict=True))
        )

    def move_value(self, game, move):
        child = game.play(move)
        if child.terminal:
            return 1.0 if child.winner == game.turn else 0.0
        return -self.value(child)

    def choose(self, game):
        moves = game.legal_moves()
        if not moves:
            raise ValueError("Cannot choose a move in a terminal game.")
        scores = {m: self.move_value(game, m) for m in moves}
        best = max(scores.values())
        return self.rng.choice([m for m in moves if scores[m] == best])

    def update(self, game, child, rate=0.03):
        prediction = self.value(game)
        target = (
            (1.0 if child.winner == game.turn else 0.0)
            if child.terminal
            else -self.value(child)
        )
        error = target - prediction
        gradient = rate * error * (1 - prediction * prediction)
        self.weights = [
            w + gradient * x for w, x in zip(self.weights, features(game), strict=True)
        ]
        return error * error

    def save(self, path, metadata=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                dict(
                    schema=1,
                    algorithm="linear-tanh-td0",
                    weights=self.weights,
                    metadata=metadata or {},
                ),
                indent=2,
            )
            + "\n"
        )

    @classmethod
    def load(cls, path=DEFAULT_MODEL, seed=0):
        data = json.loads(Path(path).read_text())
        if data.get("schema") != 1 or data.get("algorithm") != "linear-tanh-td0":
            raise ValueError("Unsupported model format.")
        return cls(data["weights"], seed)


def train(games=5000, seed=2026):
    if games < 1:
        raise ValueError("Games must be positive.")
    agent = LearningAgent(seed=seed)
    rng = random.Random(seed)
    start, errors, decisions = time.perf_counter(), 0.0, 0
    outcomes = [0, 0, 0]
    for index in range(games):
        game = Game()
        epsilon = 0.3 - 0.25 * index / max(1, games - 1)
        while not game.terminal:
            move = (
                rng.choice(game.legal_moves())
                if rng.random() < epsilon
                else agent.choose(game)
            )
            child = game.play(move)
            errors += agent.update(game, child)
            decisions += 1
            game = child
        outcomes[2 if game.winner is None else game.winner] += 1
    return agent, dict(
        games=games,
        seed=seed,
        learning_rate=0.03,
        epsilon_start=0.3,
        epsilon_end=0.05,
        seconds=time.perf_counter() - start,
        decisions=decisions,
        mean_squared_td_error=errors / decisions,
        outcomes=outcomes,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    agent, metadata = train(args.games, args.seed)
    agent.save(args.output, metadata)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
