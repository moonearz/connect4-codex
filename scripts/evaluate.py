"""Reproduce the small evaluation suite sequentially on one CPU process."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES = [
    ("minimax", "random", 20, 2026, 0),
    ("alphabeta", "random", 20, 2026, 0),
    ("mcts", "random", 20, 2026, 0),
    ("learned", "random", 100, 50000, 0),
    ("untrained", "random", 100, 50000, 0),
    ("learned", "untrained", 100, 50000, 0),
    ("learned", "minimax", 40, 50000, 0),
    ("learned", "alphabeta", 40, 50000, 0),
    ("learned", "mcts", 40, 50000, 0),
    ("alphabeta", "minimax", 40, 50000, 0),
    ("alphabeta", "mcts", 40, 50000, 0),
    ("mcts", "minimax", 40, 50000, 0),
    ("alphabeta", "minimax", 40, 50000, 4),
    ("learned", "minimax", 40, 50000, 4),
    ("learned", "alphabeta", 40, 50000, 4),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/current")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Experimental results",
        "",
        "Games alternate seats. Each pair shares seeds and, when enabled, a",
        "four-ply random opening. Timings exclude initialization and opening moves.",
        "This suite runs matches sequentially; wall time varies by machine.",
        "",
        "| Agent A | Agent B | Opening plies | Games | A wins | B wins | Draws | "
        "A ms/move | B ms/move | Raw data |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for first, second, games, seed, opening in MATCHES:
        name = f"{first}-{second}" + ("-openings" if opening else "") + ".json"
        target = args.output / name
        subprocess.run(
            [
                sys.executable,
                "-m",
                "connect4.benchmark",
                "--agents",
                first,
                second,
                "--games",
                str(games),
                "--seed",
                str(seed),
                "--opening-plies",
                str(opening),
                "--output",
                str(target),
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        result = json.loads(target.read_text())
        a, b = result["wins"]
        ta, tb = [t * 1000 for t in result["mean_move_seconds"]]
        lines.append(
            f"| {first} | {second} | {opening} | {games} | {a} | {b} | "
            f"{result['draws']} | {ta:.3f} | {tb:.3f} | [{name}]({name}) |"
        )
        print(f"{name}: {a}/{b}/{result['draws']}", flush=True)
    lines += [
        "",
        "## Interpretation and limits",
        "",
        "- This report uses the current agents and packaged model. Configuration,",
        "  source/model hashes and full move traces are recorded in each JSON file.",
        "- Empty-board deterministic matchups repeat two games. Paired random",
        "  openings provide diversity, but the two games in each pair are related.",
        "- Depth and rollout budgets differ. Compare recorded timings as well as",
        "  outcomes; these are not matched-time algorithm rankings.",
        "- The learned and untrained agents share tactical depth-6 search, with",
        "  trained versus zero feature weights. MCTS uses tactical guided rollouts.",
        "- For frozen original-agent controls and isolated search/model changes,",
        "  run scripts/compare_improvements.py and read its separate report.",
        "- Seeds and moves reproduce. Timings vary by hardware. Future research",
        "  should use multiple training seeds and larger held-out opening suites.",
    ]
    (args.output / "RESULTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
