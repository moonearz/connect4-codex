# Connect Four simulator and AI

A Python 3.13 Connect Four engine, responsive Flask application, four traditional
opponents, and a small agent trained through self-play. No production deployment
or paid services are required.

## Run locally

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
flask --app connect4.web:create_app run --port 5000
```

Open <http://127.0.0.1:5000>. Select computer or friend mode, choose a difficulty,
and use the arrow above a column to drop a disc. Column controls work with Tab
and Enter. Choose **First · Red** or **Second · Yellow** against the computer;
when you choose second, the computer opens automatically. Changing settings or
selecting **New game** resets play and keeps the chosen seat. No accounts,
database, or session secret are needed: the server reconstructs and validates
each game from its move list.
The Flask development server is for local use.

Python 3.13 can also be installed with `uv python install 3.13`. With uv available,
`uv venv --python 3.13` and `uv pip install -e '.[dev]'` provide the same setup.

## Checks

```bash
pytest -q
ruff check .
ruff format --check .
```

Make targets use `$(HOME)/.venvs/$(PROJECT)` by default, preserving the existing
local setup (`PROJECT` is the repository directory name). If you followed the
`.venv` setup above, run `make VENV=.venv test` or `make VENV=.venv check`.
`make setup` creates the default environment and also installs the repository's
pre-commit hooks via prek; use `make VENV=.venv setup` to override its location.
GitHub Actions runs pytest and Ruff on Python 3.13 for pushes and pull requests.

## Opponents

| UI choice | Implementation | Budget |
|---|---|---|
| Easy | Seeded random legal moves | One sample |
| Medium | Minimax with open-window heuristic | Depth 3 |
| Hard | Alpha-beta with the same heuristic and center-first ordering | Depth 5 |
| Monte Carlo | Tactical UCT with guided rollouts and value cutoffs | 600 iterations/move, 12-ply rollout limit |
| Learning agent | 14-feature tanh value function, trained by zero-sum TD(lambda) | Tactical depth-6 search with learned leaf values |

Web requests use fresh random seeds; experimental runs explicitly seed agents.
The learner's checked-in weights come from 12,000 epsilon-greedy self-play games
with seed 2027. Training took 41.52 seconds on one CPU process, after a 200-game
pilot estimated a 54-second budget. Training uses one-ply decisions; normal play
uses deeper search with the trained value function. There is no PyTorch/GPU,
pretrained agent, solved-game database, or downloaded game data.

MCTS takes immediate wins, blocks forced threats, and avoids enabling immediate
losses. Its rollouts use the same tactics and central-column preference, ending
with a bounded heuristic estimate after 12 plies. Agents reused across simulated
games can retain searched subtrees between moves. The stateless web API creates a
fresh agent for each request, so browser games do not reuse trees across requests.

Search budgets differ between opponents. The improvement report records time per
move and controls for search depth, learned weights, and MCTS iteration count.

## Reproduce experiments

With the virtual environment active:

```bash
# Bounded CPU self-play; overwrites the packaged learner model.
python -m connect4.learning --games 12000 --seed 2027

# One paired matchup; game count must be positive and even.
python -m connect4.benchmark --agents learned random --games 100 --seed 50000 \
  --output experiments/current/learned-random.json

# Random opening positions shared within each pair, then seats swapped.
python -m connect4.benchmark --agents alphabeta minimax --games 40 \
  --seed 50000 --opening-plies 4 --output experiments/current/alphabeta-minimax-openings.json

# Current general evaluation suite; writes experiments/current/RESULTS.md.
python scripts/evaluate.py

# Before/after comparison on held-out paired openings.
python scripts/compare_improvements.py
```

Agent names: `random`, `minimax`, `alphabeta`, `mcts`, `learned`, `untrained`.
JSON records include seeds, seats, outcomes, full move traces, draws, win rates,
decision counts, timing, algorithm budgets, Python/platform, Git revision, and
source/model SHA-256 hashes. Training JSON records weights and hyperparameters.
Fixed seeds reproduce model weights and game traces; wall times naturally differ.
The suites take a few CPU minutes. `compare_improvements.py` loads the original
agents and model from the fixed merged baseline commit in local Git history. A
shallow clone needs the baseline history fetched before running that comparison.
It compares old/new MCTS, old/new learning, the old model with new search, zero
weights with new search, and the new model without search. By default all matches
use the same held-out four-ply openings (seed 70000) with alternating seats.

See [agent improvement results](experiments/improvements/RESULTS.md) for the current
comparison, including controls that separate training gains from search gains.
The [fresh-tree web control](experiments/improvements/web/RESULTS.md) measures MCTS
without reuse between turns. Reproduce it with:

```bash
python scripts/compare_improvements.py --match mcts_fresh alphabeta \
  --output experiments/improvements/web
```

[Initial results](experiments/RESULTS.md) and their raw JSON files are
historical snapshots of the original agents. New general-suite runs write into
`experiments/current/` to preserve those snapshots. Empty-board deterministic
matchups repeat the same two games; use paired random openings for position
diversity.

## Compare with an exact solver

An optional evaluation tool runs [Pascal Pons's solver](https://github.com/PascalPons/connect4)
locally. It measures exact move quality and plays paired continuations against
perfect opposition, using the existing agents unchanged.

```bash
# Requires a C++ compiler. Downloads pinned AGPL source into ignored .solver/.
python scripts/setup_solver.py

# Random surviving midgame/endgame positions and paired continuations.
python -m connect4.solver_benchmark

# Earlier positions with no immediate win and at least two safe choices.
python -m connect4.solver_benchmark --quiet --positions 36 \
  --plies 14 15 16 17 18 19 --games 12 --seed 92000 \
  --output experiments/solver-strategic
```

See the [evaluation guide](docs/SOLVER.md), [initial solver results](experiments/solver/RESULTS.md)
and [earlier quiet-position results](experiments/solver-strategic/RESULTS.md).
The solver and its labels are evaluation-only: neither training nor browser play
uses them. No opening book is downloaded. Results include timeouts/coverage and
separate exact-score optimality from preserving the best achievable win/draw/loss.
Continuation results start at the recorded positions, rather than the empty board.

## Engine API

```python
from connect4.engine import Game, simulate
from connect4.agents import AlphaBetaAgent, RandomAgent

state = Game()
state = state.play(3)  # zero-based column; returns a new immutable state
print(state.board())  # top row first; 0=empty, 1=first player, 2=second
result = simulate(AlphaBetaAgent(depth=5), RandomAgent(seed=42))
print(result.winner)  # 0 or 1; None for a draw when terminal
```

Agents implement `choose(game) -> int` and may select only legal columns. Game
states use two sentinel bitboards for fast win detection and inexpensive copying.
Use `Game()` and `play()` to construct valid states; manually constructing arbitrary
bitboards bypasses move validation. Calling `play()` on a terminal state, a full
column, or an invalid column raises `ValueError`.

## Structure and development status

- `src/connect4/engine.py`: immutable game state, agent protocol, simulation loop.
- `agents.py`: random, minimax, alpha-beta, and MCTS implementations.
- `learning.py`: TD self-play, features, JSON model persistence, training CLI.
- `benchmark.py`: paired evaluation CLI with optional random openings.
- `solver.py`, `solver_benchmark.py`: optional external exact-reference evaluation.
- `web.py`, `templates/`, `static/`: Flask API and browser interface.
- `tests/`: engine oracle, tactical search, API and learning tests.
- `experiments/`: raw results, training pilot, and comparison report.
- `PROGRESS.md`: completed milestones, verification, and next steps.

This is a working research baseline, not perfect or solved play. Next work should
prioritize multiple training seeds, larger position suites, equal-time comparisons,
and better learned value models. A neural model is deferred until its
compute cost and experimental benefit are justified.
