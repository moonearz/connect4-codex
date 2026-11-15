"""Reproduce the small evaluation suite sequentially on one CPU process."""

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
        target = ROOT / "experiments" / name
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
        "- The trained TD model wins 99/100 against random, compared with 50/100",
        "  for the same architecture with zero weights. It wins 92/100 head-to-head",
        "  against that untrained model, showing a benefit from experience.",
        "- The learned model remains weaker than depth-limited search. Its eight",
        "  aggregate features discard spatial relationships and tactical sequences.",
        "- Empty-board deterministic search matchups repeat the same two games;",
        "  their game counts do not represent independent samples. The additional",
        "  paired-opening matches provide position diversity, but are still small.",
        "- MCTS uses 300 uniform random rollouts per decision. This is a small",
        "  budget with no rollout tactical policy or tree reuse.",
        "- Both trained and untrained models value immediate terminal wins exactly;",
        "  neither uses pretrained agents, solved databases or downloaded games.",
        "- Depths and rollout counts are different computational budgets. This is",
        "  a baseline comparison, not a matched-time algorithm ranking.",
        "- Seeds 2026–2035 cover initial random-baseline matches; held-out",
        "  evaluation uses seeds starting at 50000. Training uses seed 2026.",
        "  Outcomes and move traces reproduce; timings and timing-based hashes vary.",
        "",
        "## Next experiments",
        "",
        "1. Run multiple training seeds and larger held-out opening suites.",
        "2. Add shallow search over the learned value function and compare with",
        "   equally budgeted handcrafted evaluation.",
        "3. Add tactical rollout policies and tree reuse to MCTS.",
        "4. Consider a small PyTorch value/policy network only after estimating",
        "   CPU/GPU cost. It should retain held-out evaluations and an untrained",
        "   control. No expensive neural training was run in this milestone.",
    ]
    (ROOT / "experiments" / "RESULTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
