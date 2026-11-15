# Exact solver evaluation

The optional reference is [Pascal Pons's Connect4 solver](https://github.com/PascalPons/connect4),
pinned at revision `d6ba50d8aaf2308c769d9bf2abd42d90f34baf41`. It computes exact
per-column scores using its strong solver. This project runs it as a standalone
subprocess for evaluation, without an opening book. It is not a playable web
opponent and is never imported by the agents, engine or learning code.

## Build the optional executable

Use Python 3.13 and a C++ compiler (`g++`, with C++11 support):

```bash
. .venv/bin/activate
python scripts/setup_solver.py
```

This explicitly downloads a pinned, SHA-256-verified source archive from GitHub,
compiles the upstream `main.cpp` and `Solver.cpp`, and records compiler flags,
source hashes and the binary hash in `.solver/manifest.json`. It does not execute
upstream build scripts or change the application's dependencies or Makefile.
A custom compiler/location can be supplied with `--compiler` and `--destination`.
The upstream transposition table uses roughly 80 MiB; only one query runs at a time.

Upstream code is **AGPL-3.0-or-later**. Its original source, copyright notices and
`LICENSE` are retained in the ignored `.solver/` cache. Source and executable are
not vendored or distributed with the Python package. Keep upstream notices and
license obligations in mind if separately redistributing that solver. Building it
does not select or change this project's license.

## Reproduce the evaluation

```bash
python -m connect4.solver_benchmark
```

Defaults are:

- Agents: random, minimax, alpha-beta, MCTS and learned search, all unchanged.
- Seed 90000, separate from training and earlier development/evaluation seeds.
- 90 distinct nonterminal positions: 15 each after 20, 21, 24, 25, 28 and 29 plies.
  Even/odd stages cover both players to move. Positions come from random legal
  games; games terminating before the requested stage are rejected. Positions
  with fewer than two legal choices and duplicate boards are rejected. Selection
  does not use solver scores or agent performance.
- A fresh seeded agent makes one decision per position. All agents use the same
  resolved position subset; every move's exact reference scores are recorded.
- 20 game continuations per agent from the first ten corpus positions, with two
  games per opening and the agent assigned to each color. Those ten openings are
  an intentionally small sample and are also part of the move-quality corpus.
- Three-second wall timeout per exact query. Timeouts are never approximated.
- JSON checkpoints and the final Markdown report go into `experiments/solver/`.

For a different budget or stage range:

```bash
python -m connect4.solver_benchmark --positions 30 --games 10 --timeout 5 \
  --plies 16 17 20 21 24 25 --seed 91000 --output experiments/solver-custom

# Move-quality evaluation only; no continuation games.
python -m connect4.solver_benchmark --games 0 --agents alphabeta learned
```

Earlier positions can take much longer without an opening book. Empty-board
analysis is supported (`--positions 1 --plies 0 --games 2`), but can time out even
with a large budget. Default results describe **midgame/endgame strength**, not
full-game strength from the initial board. No website is queried during evaluation.

### Earlier quiet-position comparison

The additional recorded suite rejects positions with an immediate winning move
and requires at least two legal moves that do not allow an immediate opponent
win. This filter uses the engine only, without solver labels or agent decisions.

```bash
python -m connect4.solver_benchmark --quiet --positions 36 \
  --plies 14 15 16 17 18 19 --games 12 --seed 92000 \
  --output experiments/solver-strategic
```

This has six positions per stage and uses the first six for paired continuations.
It tests earlier strategic decisions and is intentionally more expensive. The
three-second query limit remains in effect; interpret results on the resolved
subset alongside the coverage/timeout counts. Timed-out positions may be harder,
so the resolved subset is not an unbiased estimate of every earlier position.

## Metrics

The solver uses one-based columns on stdin; our adapter validates and translates
zero-based engine moves and checks its echoed position, seven returned scores,
legal/full columns, score ranges and exit status. Positive/zero/negative scores
mean a forced win/draw/loss for the player to move. Raw score differences also
reflect speed: higher scores prefer faster wins and delay forced losses. They
are solver score units, not Elo ratings or centipawns.

- **Exact-score optimal rate:** chosen move equals the best exact solver score.
- **Outcome preservation:** chosen move preserves the best achievable W/D/L,
  allowing slower wins or faster unavoidable losses.
- **Informative outcome preservation:** the same metric restricted to positions
  whose legal moves have different W/D/L outcomes. Overall preservation can look
  high when all legal moves already lose; this subset exposes avoidable mistakes.
- **Transitions:** win-to-draw, win-to-loss and draw-to-loss errors are recorded
  separately, along with exact-score and outcome regret.
- **Continuation W/D/L:** actual terminal outcomes against perfect opposition.
  Each record includes the initial achievable result for that agent, color,
  trace, perfect opponent's scores/choices and points lost from perfect play.
  A loss from an already-lost start is distinguished from squandering a win/draw.
- Position-stage breakdowns, agent decision time, solved coverage, aborted games,
  solver timings and build/source/model provenance are retained in JSON.

The two games in an opening pair are related; these small samples should not be
read as independent-game confidence intervals or proof of a universal ranking.
Agents use different computational budgets. Static decisions use fresh agents;
continuations retain each agent within a game (including MCTS subtree reuse).

Unresolved opening positions are excluded identically from every agent's static
scores. A continuation timing out is marked aborted, with its partial trace, and
is never counted as a loss or draw. Protocol errors fail the run instead of
producing guessed results. Checkpoints marked `running` are incomplete.

## Tests and boundaries

```bash
pytest -q tests/test_solver.py
pytest -q
```

Tests cover protocol/column conversion, cache behavior, legality, process errors,
timeouts, score/outcome semantics, paired seats, full traces and perfect-play
bounds. When `.solver/c4solver` exists, an additional integration test compares
all its legal-move scores on ten small endgames with independent full-width
Python minimax. Without the optional binary, only that integration test skips;
normal CI needs no compiler, network or downloaded solver.

All generated solver labels are **evaluation-only holdout data**. Neither the
learning pipeline nor deployed agents read `experiments/solver`, invoke the
reference, or use solved-game databases. This evaluation must not become training
input if its reported performance is to remain a held-out measurement.

## Recorded snapshot and next steps

The initial 90-position suite had 50 informative positions. On the harder
36-position quiet suite, 23 were informative. Outcome-preserving choices on
those 23 were: random 8, minimax 17, alpha-beta 18, MCTS 20 and learner 18.
All 126 initial positions resolved, and all 160 continuations completed, with no
solver timeouts. These totals cover two small, differently selected corpora.

MCTS and the learner each converted all five winning starts in the quieter
continuation sample, but both lost the two drawable starts. That identifies draw
preservation as a useful area to investigate. Neither agent is perfect: MCTS
still made three outcome-changing errors on the 36 quiet positions. Its stronger
showing here also comes with a larger time budget than alpha-beta.

Use larger position sets and additional seeds before drawing general strength
conclusions. If these cases guide future tuning, treat them as development data
and create a fresh held-out set for the next reported comparison.
