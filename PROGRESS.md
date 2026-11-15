# Development log

## Phase 1
- Implemented immutable sentinel bitboards and a shared agent protocol.
- Added direction, gravity, validation, terminal, and randomized independent grid-oracle tests.
- Python 3.13 installed locally; development environment lives in `.venv`.

## Phase 2
- Added responsive Flask interface with friend/computer modes, reset, keyboard-accessible column controls, and server-side replay validation.
- Added API integration tests covering malformed inputs, terminal games, reset, and computer replies.
- Validation: 25 tests passed; Ruff passed. Difficulty choices will be connected to search agents in Phase 3.

## Phase 3
- Added random, minimax (depth 3), alpha-beta (depth 5), and UCT MCTS (300 iterations) opponents.
- Added paired, seeded benchmarking with per-game outcomes, seat assignments, decision counts and timing.
- Search tactical tests, pruning equivalence, repeatability and benchmarking tests pass (33 tests total); Ruff passes.
- Initial 20-game comparisons: minimax and alpha-beta each won 20/20 against random. These small samples establish a baseline, not solved play.
