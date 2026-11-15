# Agent improvements

Baseline revision: `a70bc307e2e4e31ba5862e0be257b921b54e7e1f`.
Run `python scripts/compare_improvements.py`
to reproduce. Each matchup uses the same held-out seeded four-ply openings
and alternates seats within pairs. Evaluation runs sequentially.

| Agent A | Agent B | Games | A wins | B wins | Draws | A ms/move | B ms/move | Data |
|---|---|---:|---:|---:|---:|---:|---:|---|
| mcts_fresh | alphabeta | 40 | 23 | 17 | 0 | 98.274 | 8.720 | [mcts_fresh-alphabeta.json](mcts_fresh-alphabeta.json) |

## What changed

- MCTS takes immediate wins, blocks single threats, and avoids enabling
  an immediate opponent win. Rollouts share these checks, prefer central
  columns and stop after 12 plies with a bounded heuristic estimate.
  UCT exploration is 0.7; simulated agents can reuse searched subtrees.
- Learning adds playable/unsupported winning-cell counts and double-threat
  indicators to the original eight features. Alternating-sign eligibility
  traces (lambda 0.7) propagate rewards through zero-sum self-play.
- The new model trained for 12,000 games with seed 2027, alpha 0.03, and
  epsilon decreasing from 0.3 to 0.05. Training uses one-ply decisions;
  deployed play uses tactical depth-6 alpha-beta with learned leaf values.
  Training took 41.52 seconds on one CPU process (200-game pilot: 0.90 s).

## Controls and limitations

- `old_model_search` isolates search changes from feature/training changes.
  `untrained_search` checks how much search can accomplish with zero weights.
  `learned_policy` removes search to test the new model itself.
- `mcts_300` checks the new algorithm at the old iteration count. Guided
  rollouts cost more per iteration, so this is not an equal-time control.
- These are small paired samples, not proof of general superiority. Both
  games in a pair share an opening; do not treat all games as independent.
- Development used 10-game pilots at seed 61000. Final evaluation uses
  seeds starting at 70000, separated from training and development.
- Web requests are stateless and create a fresh agent each move. Subtree
  reuse is available in simulations, but not across browser requests.
  mcts_fresh resets its tree each turn to test this web behavior.
  Depth and iteration budgets are deterministic; timings vary by hardware.
- The stronger learner includes search; it is not a claim that the small
  value model alone replaces alpha-beta. No neural model or GPU was used.
