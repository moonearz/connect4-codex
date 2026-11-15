"""Small zero-sum TD(lambda) value model trained by epsilon-greedy self-play."""

import argparse
import json
import math
import random
import time
from pathlib import Path

from connect4.agents import WINDOWS, MinimaxAgent
from connect4.engine import Game
from connect4.tactics import winning_spots

DEFAULT_MODEL = Path(__file__).parent / "data" / "learner.json"


def features(game, version=2):
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
    if version == 2:
        occupied = own | other
        playable = sum(1 << (c * 7 + h) for c, h in enumerate(game.heights) if h < 6)
        threats = [winning_spots(b, occupied) for b in (own, other)]
        immediate = [(spots & playable).bit_count() for spots in threats]
        counts += [n / 2 for n in immediate]
        counts += [(spots & ~playable).bit_count() / 8 for spots in threats]
        counts += [float(n >= 2) for n in immediate]
    return counts


class LearningAgent:
    def __init__(self, weights=None, seed=0, depth=6):
        self.weights = list(weights) if weights is not None else [0.0] * 14
        if len(self.weights) not in (8, 14) or not all(
            math.isfinite(w) for w in self.weights
        ):
            raise ValueError(
                "Expected eight legacy or fourteen current finite feature weights."
            )
        self.feature_version = 1 if len(self.weights) == 8 else 2
        self.rng = random.Random(seed)
        self.depth = depth
        self.search = MinimaxAgent(
            depth,
            pruning=True,
            evaluator=lambda game: 1000 * self.value(game),
            tactical=True,
        )

    def value(self, game):
        return math.tanh(
            sum(
                w * x
                for w, x in zip(
                    self.weights, features(game, self.feature_version), strict=True
                )
            )
        )

    def move_value(self, game, move):
        child = game.play(move)
        if child.terminal:
            return 1.0 if child.winner == game.turn else 0.0
        return -self.value(child)

    def choose(self, game):
        if self.depth > 1:
            return self.search.choose(game)
        moves = game.legal_moves()
        if not moves:
            raise ValueError("Cannot choose a move in a terminal game.")
        scores = {m: self.move_value(game, m) for m in moves}
        best = max(scores.values())
        return self.rng.choice([m for m in moves if scores[m] == best])

    def update(self, game, child, rate=0.03, traces=None, trace_decay=0.7):
        prediction = self.value(game)
        target = (
            (1.0 if child.winner == game.turn else 0.0)
            if child.terminal
            else -self.value(child)
        )
        error = target - prediction
        gradient = [
            (1 - prediction * prediction) * x
            for x in features(game, self.feature_version)
        ]
        if traces is not None:
            # Values change perspective each ply, so traces alternate sign.
            traces[:] = [
                g - trace_decay * old for g, old in zip(gradient, traces, strict=True)
            ]
            gradient = traces
        self.weights = [
            w + rate * error * g for w, g in zip(self.weights, gradient, strict=True)
        ]
        return error * error

    def save(self, path, metadata=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                dict(
                    schema=2,
                    feature_version=self.feature_version,
                    algorithm="linear-tanh-td-lambda",
                    weights=self.weights,
                    metadata=metadata or {},
                ),
                indent=2,
            )
            + "\n"
        )

    @classmethod
    def load(cls, path=DEFAULT_MODEL, seed=0, depth=6):
        data = json.loads(Path(path).read_text())
        if data.get("schema") not in (1, 2) or data.get("algorithm") not in (
            "linear-tanh-td0",
            "linear-tanh-td-lambda",
        ):
            raise ValueError("Unsupported model format.")
        return cls(data["weights"], seed, depth=depth)


def train(games=5000, seed=2026):
    if games < 1:
        raise ValueError("Games must be positive.")
    agent = LearningAgent(seed=seed, depth=1)
    rng = random.Random(seed)
    start, errors, decisions = time.perf_counter(), 0.0, 0
    outcomes = [0, 0, 0]
    for index in range(games):
        game = Game()
        traces = [0.0] * len(agent.weights)
        epsilon = 0.3 - 0.25 * index / max(1, games - 1)
        while not game.terminal:
            move = (
                rng.choice(game.legal_moves())
                if rng.random() < epsilon
                else agent.choose(game)
            )
            child = game.play(move)
            errors += agent.update(game, child, traces=traces)
            decisions += 1
            game = child
        outcomes[2 if game.winner is None else game.winner] += 1
    return agent, dict(
        games=games,
        seed=seed,
        learning_rate=0.03,
        trace_decay=0.7,
        feature_version=2,
        training_search_depth=1,
        play_search_depth=6,
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
