# Exact-solver evaluation

Reference: Pascal Pons Connect4 solver, strong analysis, no opening book.
Move outcomes are from the player-to-move perspective. The corpus was
generated from seeded random legal games, rejecting terminal games and
duplicates. No positions were selected by solver outcome.

| Agent | Scored | Exact-score optimal | Outcome preserved | Informative outcome preserved | Continuation W/D/L | Aborted |
|---|---:|---:|---:|---:|---|---:|
| random | 36 | 30.6% | 58.3% | 34.8% | 0/0/12 | 0 |
| minimax | 36 | 61.1% | 83.3% | 73.9% | 2/1/9 | 0 |
| alphabeta | 36 | 80.6% | 86.1% | 78.3% | 4/0/8 | 0 |
| mcts | 36 | 83.3% | 91.7% | 87.0% | 5/0/7 | 0 |
| learned | 36 | 80.6% | 86.1% | 78.3% | 5/0/7 | 0 |

Seed: 92000; stages (plies): [14, 15, 16, 17, 18, 19].
Coverage: 36/36 positions solved; 23 informative positions. Starting outcomes: {'win': 22, 'draw': 4, 'loss': 10}.

Quiet-position filter: no immediate win and at least two moves
that avoid an immediate opponent win. This uses local tactical
checks only, not solver scores or agent performance.

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
