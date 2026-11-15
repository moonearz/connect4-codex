# Exact-solver evaluation

Reference: Pascal Pons Connect4 solver, strong analysis, no opening book.
Move outcomes are from the player-to-move perspective. The corpus was
generated from seeded random legal games, rejecting terminal games and
duplicates. No positions were selected by solver outcome.

| Agent | Scored | Exact-score optimal | Outcome preserved | Informative outcome preserved | Continuation W/D/L | Aborted |
|---|---:|---:|---:|---:|---|---:|
| random | 90 | 28.9% | 70.0% | 46.0% | 3/0/17 | 0 |
| minimax | 90 | 96.7% | 96.7% | 94.0% | 9/0/11 | 0 |
| alphabeta | 90 | 98.9% | 98.9% | 98.0% | 9/1/10 | 0 |
| mcts | 90 | 95.6% | 100.0% | 100.0% | 10/0/10 | 0 |
| learned | 90 | 97.8% | 97.8% | 96.0% | 9/1/10 | 0 |

Seed: 90000; stages (plies): [20, 21, 24, 25, 28, 29].
Coverage: 90/90 positions solved; 50 informative positions. Starting outcomes: {'win': 62, 'loss': 28}.

## Reading the results

- Exact-score optimal means the move has the best solver score, including
  its preference for faster wins and slower losses.
- Outcome preservation accepts any move retaining the best achievable
  win/draw/loss. It does not penalize a slower forced win.
- Informative positions have legal moves with different win/draw/loss
  outcomes. Already-lost positions can inflate the overall preservation
  rate; use this subset and the recorded transitions to assess blunders.
- W/D/L describes complete continuations from sampled midgame positions,
  not games from an empty board. Each opening is played twice, assigning
  the agent to each color. Raw records include each starting position's
  perfect-play outcome and how many attainable points the agent lost.
- Timeouts are unresolved or aborted, never losses, draws or heuristic
  answers. All agents share the same resolved move-quality subset.
- These are small samples, not Elo ratings. Different starting stages and
  outcome distributions can change the ranking. Late positions are easier
  for finite-depth agents; the report does not establish opening strength.
- The oracle is evaluation-only. Agents, training, and the web app do not
  use it or its labels. No opening book or pretrained agent was downloaded.

See `results.json` for seeds, full positions/scores, decisions, game
traces, timeout counts, build/source/model hashes and computational budgets.
