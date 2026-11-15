"""Compare new agents with frozen pre-change agents on shared held-out openings.

Requires the baseline commit in local Git history (fetch full history for a
shallow clone). Only code from the fixed, reviewed project revision is loaded.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

from connect4.agents import MCTSAgent, make_agent
from connect4.benchmark import add_provenance, benchmark
from connect4.learning import LearningAgent

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "a70bc307e2e4e31ba5862e0be257b921b54e7e1f"
MATCHES = [
    ("old_mcts", "alphabeta"),
    ("mcts", "alphabeta"),
    ("mcts_300", "alphabeta"),
    ("old_learned", "alphabeta"),
    ("learned", "alphabeta"),
    ("old_model_search", "alphabeta"),
    ("untrained_search", "alphabeta"),
    ("learned_policy", "old_learned"),
    ("learned", "mcts"),
]


def baseline_file(path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)


def load_baseline(path, name):
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / path)
    sys.modules[name] = module
    source = baseline_file(path)
    exec(compile(source, f"{BASELINE}:{path}", "exec"), module.__dict__)
    return module, hashlib.sha256(source).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=40)
    parser.add_argument("--seed", type=int, default=70000)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "experiments/improvements"
    )
    args = parser.parse_args()
    old_agents, agents_hash = load_baseline("src/connect4/agents.py", "baseline_agents")
    old_learning, learning_hash = load_baseline(
        "src/connect4/learning.py", "baseline_learning"
    )
    old_model_bytes = baseline_file("src/connect4/data/learner.json")
    old_model = json.loads(old_model_bytes)

    def factory(name, seed):
        if name == "old_mcts":
            return old_agents.MCTSAgent(300, seed)
        if name == "mcts_300":
            return MCTSAgent(300, seed)
        if name == "old_learned":
            return old_learning.LearningAgent(old_model["weights"], seed)
        if name == "old_model_search":
            return LearningAgent(old_model["weights"], seed, depth=6)
        if name == "untrained_search":
            return LearningAgent(seed=seed, depth=6)
        if name == "learned_policy":
            return LearningAgent.load(seed=seed, depth=1)
        return make_agent(name, seed)

    args.output.mkdir(parents=True, exist_ok=True)
    rows = [
        "# Agent improvements",
        "",
        f"Baseline revision: `{BASELINE}`. Run `python scripts/compare_improvements.py`",
        "to reproduce. Each matchup uses the same held-out seeded four-ply openings",
        "and alternates seats within pairs. Evaluation runs sequentially.",
        "",
        "| Agent A | Agent B | Games | A wins | B wins | Draws | A ms/move | B ms/move | Data |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for first, second in MATCHES:
        result = add_provenance(
            benchmark(
                first, second, args.games, args.seed, factory=factory, opening_plies=4
            )
        )
        result["baseline"] = dict(
            revision=BASELINE,
            agents_sha256=agents_hash,
            learning_sha256=learning_hash,
            model_sha256=hashlib.sha256(old_model_bytes).hexdigest(),
        )
        result["controls"] = {
            "old_mcts": "Original UCT, 300 uniform random rollouts",
            "mcts": "Tactical UCT, 600 bounded guided rollouts, subtree reuse",
            "mcts_300": "New MCTS at original 300-iteration budget",
            "old_learned": "Original eight-feature model, one-ply selection",
            "learned": "New 14-feature TD(lambda) model, tactical depth-6 search",
            "old_model_search": "Original learned weights with new depth-6 search",
            "untrained_search": "Zero weights with new depth-6 search",
            "learned_policy": "New trained model with one-ply selection",
            "alphabeta": "Unchanged depth-5 handcrafted evaluation",
        }
        name = f"{first}-{second}.json"
        (args.output / name).write_text(json.dumps(result, indent=2) + "\n")
        a, b = result["wins"]
        ta, tb = [x * 1000 for x in result["mean_move_seconds"]]
        rows.append(
            f"| {first} | {second} | {args.games} | {a} | {b} | "
            f"{result['draws']} | {ta:.3f} | {tb:.3f} | [{name}]({name}) |"
        )
        print(f"{first}/{second}: {a}/{b}/{result['draws']}", flush=True)
    rows += [
        "",
        "## What changed",
        "",
        "- MCTS takes immediate wins, blocks single threats, and avoids enabling",
        "  an immediate opponent win. Rollouts share these checks, prefer central",
        "  columns and stop after 12 plies with a bounded heuristic estimate.",
        "  UCT exploration is 0.7; simulated agents can reuse searched subtrees.",
        "- Learning adds playable/unsupported winning-cell counts and double-threat",
        "  indicators to the original eight features. Alternating-sign eligibility",
        "  traces (lambda 0.7) propagate rewards through zero-sum self-play.",
        "- The new model trained for 12,000 games with seed 2027, alpha 0.03, and",
        "  epsilon decreasing from 0.3 to 0.05. Training uses one-ply decisions;",
        "  deployed play uses tactical depth-6 alpha-beta with learned leaf values.",
        "  Training took 41.52 seconds on one CPU process (200-game pilot: 0.90 s).",
        "",
        "## Controls and limitations",
        "",
        "- `old_model_search` isolates search changes from feature/training changes.",
        "  `untrained_search` checks how much search can accomplish with zero weights.",
        "  `learned_policy` removes search to test the new model itself.",
        "- `mcts_300` checks the new algorithm at the old iteration count. Guided",
        "  rollouts cost more per iteration, so this is not an equal-time control.",
        "- These are small paired samples, not proof of general superiority. Both",
        "  games in a pair share an opening; do not treat all games as independent.",
        "- Development used 10-game pilots at seed 61000. Final evaluation uses",
        "  seeds starting at 70000, separated from training and development.",
        "- Web requests are stateless and create a fresh agent each move. Subtree",
        "  reuse is available in simulations, but not across browser requests.",
        "  Depth and iteration budgets are deterministic; timings vary by hardware.",
        "- The stronger learner includes search; it is not a claim that the small",
        "  value model alone replaces alpha-beta. No neural model or GPU was used.",
    ]
    (args.output / "RESULTS.md").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
