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

## Phase 4
- Implemented an eight-feature tanh value model using zero-sum TD(0) self-play, with seeded exploration and JSON persistence. No pretrained data, GPU or neural-network dependency.
- Pilot: 100 games in 0.31 CPU-wall seconds, estimating ~31 seconds for 10,000 games. Bounded run completed 10,000 games in 18.62 seconds (156,933 decisions).
- Learning tests verify reward direction, changed weights, exact seeded reproduction, feature reflection symmetry and model round trips. Validation: 37 tests passed; Ruff passed.
- Browser preview tooling returned `Browser Use could not read requirements` before navigating. Visual browser verification remains outstanding; API integration tests pass.

## Evaluation and verification
- Held-out seed 50,000: learned/random 99–1; untrained/random 50–50; learned/untrained 92–8 (100 games each).
- Learned/minimax 0–40; learned/alpha-beta 0–40; learned/MCTS 12–28. Learning improves over zero weights, but this model does not match search.
- Alpha-beta/MCTS 31–8 with one draw; MCTS/minimax 13–24 with three draws (40 games each).
- Added optional seeded paired opening positions to avoid repeating only two deterministic games. Added full move traces and source/model hashes to experimental records.
- Recovered browser verification using desktop controls: verified computer reply, friend-mode turns, reset, and a ~500-pixel-wide responsive layout. Saved a preview screenshot outside the repository.
- Added Python 3.13 GitHub Actions checks and aligned Makefile's default venv with the documented local environment.
