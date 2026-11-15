# Four — Connect Four simulator and AI

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
and Enter. Changing modes/difficulty or selecting **Start fresh** resets play.
Humans play first against the computer. No accounts, database, or session secret
are needed: the server reconstructs and validates each game from its move list.
The Flask development server is for local use.

Python 3.13 can also be installed with `uv python install 3.13`. With uv available,
`uv venv --python 3.13` and `uv pip install -e '.[dev]'` provide the same setup.

## Checks

```bash
pytest -q
ruff check .
ruff format --check .
```

`make test` uses `.venv` by default; override with `VENV=/path/to/venv`.
`make setup` also installs the repository's pre-commit hooks via prek.
GitHub Actions runs pytest and Ruff on Python 3.13 for pushes and pull requests.

## Opponents

| UI choice | Implementation | Budget |
|---|---|---|
| Easy | Seeded random legal moves | One sample |
| Medium | Minimax with open-window heuristic | Depth 3 |
| Hard | Alpha-beta with the same heuristic and center-first ordering | Depth 5 |
| Explorer | UCT Monte Carlo Tree Search | 300 iterations/move |
| Learner | Eight-feature tanh value function, trained by zero-sum TD(0) | One-ply value selection |

Web requests use fresh random seeds; experimental runs explicitly seed agents.
The learner's checked-in weights come from 10,000 epsilon-greedy self-play games
with seed 2026. Training took 18.62 seconds in the development environment. It uses
no PyTorch/GPU, pretrained agents, solved-game database, or downloaded game data.
It learns feature weights from rewards; the handcrafted feature definitions and
exact evaluation of immediate terminal wins are shared with its untrained control.

## Reproduce experiments

With the virtual environment active:

```bash
# Bounded CPU self-play; overwrites the packaged learner model.
python -m connect4.learning --games 10000 --seed 2026

# One paired matchup; game count must be positive and even.
python -m connect4.benchmark --agents learned random --games 100 --seed 50000 \
  --output experiments/learned-random.json

# Random opening positions shared within each pair, then seats swapped.
python -m connect4.benchmark --agents alphabeta minimax --games 40 \
  --seed 50000 --opening-plies 4 --output experiments/alphabeta-minimax-openings.json

# Full small evaluation suite, run sequentially; regenerates RESULTS.md.
python scripts/evaluate.py
```

Agent names: `random`, `minimax`, `alphabeta`, `mcts`, `learned`, `untrained`.
JSON records include seeds, seats, outcomes, full move traces, draws, win rates,
decision counts, timing, algorithm budgets, Python/platform, Git revision, and
source/model SHA-256 hashes. Training JSON records weights and hyperparameters.
Fixed seeds reproduce model weights and game traces; wall times naturally differ.
The complete small suite takes roughly a minute on this development CPU.

See [experimental results](experiments/RESULTS.md) for comparisons and limitations.
The trained agent won 99/100 games against random versus 50/100 for its untrained
control, and won 92/100 against that control directly. It remains weaker than the
traditional search agents. Empty-board deterministic matchups repeat the same two
games; paired random openings are included to broaden the comparison.

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
- `web.py`, `templates/`, `static/`: Flask API and browser interface.
- `tests/`: engine oracle, tactical search, API and learning tests.
- `experiments/`: raw results, training pilot, and comparison report.
- `PROGRESS.md`: completed milestones, verification, and next steps.

This is a working research baseline, not perfect or solved play. Next work should
prioritize multiple training seeds, stronger position suites, learned evaluation
inside search, and tactical MCTS rollouts. A neural model is deferred until its
compute cost and experimental benefit are justified.
