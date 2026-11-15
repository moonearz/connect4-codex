"""Run reproducible paired evaluations: python -m connect4.benchmark."""

import argparse
import hashlib
import json
import platform
import random
import subprocess
import time
from pathlib import Path

from connect4.agents import make_agent
from connect4.engine import Game


def benchmark(first, second, games=20, seed=0, factory=make_agent, opening_plies=0):
    if games < 2 or games % 2:
        raise ValueError("Use a positive even game count for balanced starts.")
    if not 0 <= opening_plies <= 6:
        raise ValueError("Opening plies must be between zero and six.")
    records = []
    for index in range(games):
        # Each seed produces a pair with the same agent seeds and swapped seats.
        pair_seed = seed + index // 2
        agents = [factory(first, pair_seed), factory(second, pair_seed)]
        seats = (0, 1) if index % 2 == 0 else (1, 0)
        game, times, counts = Game(), [0.0, 0.0], [0, 0]
        opening = []
        rng = random.Random(pair_seed)
        for _ in range(opening_plies):
            move = rng.choice(game.legal_moves())
            opening.append(move)
            game = game.play(move)
        played = opening.copy()
        while not game.terminal:
            who = seats[game.turn]
            start = time.perf_counter()
            move = agents[who].choose(game)
            times[who] += time.perf_counter() - start
            counts[who] += 1
            played.append(move)
            game = game.play(move)
        records.append(
            dict(
                seed=pair_seed,
                opening_moves=opening,
                seats=seats,
                winner=None if game.winner is None else seats[game.winner],
                moves=len(played),
                played_moves=played,
                seconds=times,
                decisions=counts,
            )
        )
    wins = [sum(r["winner"] == i for r in records) for i in (0, 1)]
    draws = sum(r["winner"] is None for r in records)
    seconds = [sum(r["seconds"][i] for r in records) for i in (0, 1)]
    decisions = [sum(r["decisions"][i] for r in records) for i in (0, 1)]
    return dict(
        agents=[first, second],
        games=games,
        seed=seed,
        opening_plies=opening_plies,
        wins=wins,
        draws=draws,
        win_rates=[w / games for w in wins],
        draw_rate=draws / games,
        seconds=seconds,
        mean_move_seconds=[seconds[i] / decisions[i] for i in (0, 1)],
        records=records,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", nargs=2, default=["alphabeta", "random"])
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--opening-plies", type=int, default=0)
    parser.add_argument(
        "--output", type=Path, default=Path("experiments/benchmark.json")
    )
    args = parser.parse_args()
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        revision = "unknown"
    result = benchmark(
        *args.agents, args.games, args.seed, opening_plies=args.opening_plies
    )
    result["configuration"] = {
        "minimax_depth": 3,
        "alphabeta_depth": 5,
        "mcts_iterations": 300,
    }
    source = Path(__file__).parent
    result["source_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(source.glob("*.py"))
    }
    model = source / "data" / "learner.json"
    if "learned" in args.agents:
        result["model_sha256"] = hashlib.sha256(model.read_bytes()).hexdigest()
    result["environment"] = dict(
        python=platform.python_version(),
        platform=platform.platform(),
        revision=revision,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
