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

## Completed milestone
- All four phases have a working baseline: engine, web application, traditional agents, and a learning opponent.
- Final validation: Python 3.13.18, 45 passing tests, `ruff check .`, `ruff format --check .`, `node --check src/connect4/static/app.js`, and `git diff --check`.
- Re-ran the complete evaluation sequentially using `python scripts/evaluate.py`; raw records and `experiments/RESULTS.md` include all comparisons.
- Four-ply varied openings (40 games): alpha-beta/minimax 34–6; learned/minimax 8–32; learned/alpha-beta 3–37. This exposes variation hidden by deterministic empty-board repeats.
- Engine throughput: 10,000 random-vs-random games in 1.11 seconds (~9,008 games/second). Reproduce with `RandomAgent(777)` and `RandomAgent(778)`, reused across 10,000 calls to `simulate`, timing the loop with `time.perf_counter()`.
- Model training is bounded and CPU-only; no substantial compute spending or production deployment occurred.

## Outstanding limitations and recommended next steps
- Baseline learning model is intentionally small and weaker than search; use more training seeds and stronger held-out position sets before drawing general conclusions.
- Search uses fixed depth/iteration limits; no transposition table or MCTS tree reuse yet.
- Add learned-value lookahead, tactical MCTS rollouts and equal-time comparisons before considering a neural network.
- Browser smoke checks were manual through desktop controls because the browser automation adapter failed to read requirements. No automated browser regression suite is included.
- The UI currently assigns humans the first move; starting-seat selection is a useful follow-up.
- No deployment was attempted. GitHub CI is configured; its remote result is independent of local validation.

## Local environment compatibility correction
- Restored the original Makefile default, `$(HOME)/.venvs/$(PROJECT)`, to preserve the existing local setup.
- Updated README instructions to use `VENV=.venv` explicitly for the project-local environment used during development.

## Follow-up: seat selection, simpler interface and stronger opponents
- Added a human seat setting to the API and browser: first/red or second/yellow, with automatic computer openings and seat-aware turn, winner and color labels. Reset preserves the selected seat; friend mode hides the seat control.
- Removed the hero, promotional taglines and footer; kept a plain title, game controls and a short rules hint.
- Added tactical bitboard checks verified against brute-force move/reply enumeration in seeded games.
- MCTS now uses forced-win/block checks, avoids enabling immediate losses, guides and bounds rollouts, and reuses searched subtrees in simulations. Default budget is 600 iterations.
- The learner now has 14 features, zero-sum eligibility traces and tactical depth-6 search using learned leaf values. Original eight-feature model files still load.
- Training cost estimate: 200-game pilot took 0.90 seconds; 12,000 games estimated at 54 seconds. The bounded CPU run completed in 41.52 seconds with seed 2027.
- Development pilots (seed 61000, 10 games with paired four-ply openings): new MCTS/alpha-beta 6–3–1; new learner/alpha-beta 7–3–0; old learned weights with new search/alpha-beta 3–6–1. Final evaluation will use separate seeds (70000+).
- Added a reproducible comparison script loading original controls from the fixed merged baseline revision. Historical initial results remain in place.
- Browser smoke checks through desktop controls verified automatic openings, yellow moves and replies, reset, friend mode, and a narrow layout.
