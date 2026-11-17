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

### Follow-up results and validation
- Final paired evaluation uses seed 70000, 40 games per matchup, and the same four-ply opening positions for every control. Baseline source/model are loaded from merged revision `a70bc307e2e4e31ba5862e0be257b921b54e7e1f`.
- Against unchanged depth-5 alpha-beta: original MCTS 9–30–1; new MCTS 23–16–1; new MCTS at 300 iterations 22–17–1; fresh-tree MCTS (web control) 23–17–0. W–L–D counts are for the tested agent.
- Against alpha-beta: original learner 6–34–0; new learner 23–13–4; old learned weights with new depth-6 search 21–19–0; zero weights with new search 15–23–2.
- New model without deeper search beat the old model 25–15–0. Full learned search lost to improved MCTS 13–26–1. Search accounts for much of the learner improvement; neither result proves general superiority from these small paired samples.
- Mean simulated move times: new MCTS ~96 ms versus alpha-beta ~9 ms; new learner ~21 ms versus alpha-beta ~10 ms. The comparison records budgets and timing rather than claiming equal-time strength.
- Added reproducible frozen-baseline, original-budget, zero-weight, old-model/new-search and fresh-tree controls. Reports/raw traces are in `experiments/improvements/`; historical results were preserved. General evaluation now writes to `experiments/current/` and no longer emits hardcoded initial performance claims.
- Validation: 72 pytest tests pass on Python 3.13.18; Ruff lint/format, JavaScript syntax and diff whitespace checks pass. Wheel packaging verified tactical helpers, seat controls and the v2 trained model.
- Browser checks verified second-seat opening/replies/reset, friend-mode control hiding, correct red/yellow labels, simplified desktop page and narrow layout.
- The existing Makefile virtual environment default and project dependencies were preserved. No deployment, GPU training or paid services were used.

### Recommended next experiments
- Use additional training seeds and larger paired opening sets, with equal-time budgets for fairer strength comparisons.
- Explore learned spatial features or a small neural evaluator after estimating its compute cost; the current learner remains a compact linear value model combined with search.
- Optimize tactical rollout overhead and consider persistent web-game agents only if tree reuse is worth introducing server-side game state.

## Exact solver evaluation
- Added an optional independent Pascal Pons reference executable from pinned revision `d6ba50d8aaf2308c769d9bf2abd42d90f34baf41`. The setup script verifies the archive SHA-256, compiles explicit upstream C++ files, retains its AGPL source/license in an ignored cache and records build provenance. No upstream source/binary or opening database is shipped with the application.
- Added a bounded subprocess adapter with strict position/score/legality validation, caching, explicit no-book mode and timeout/error handling. This adapter is evaluation-only; gameplay and training are unchanged.
- Added a seeded corpus generator, exact-score/outcome-preservation/blunder metrics, stage breakdowns and paired perfect-opposition continuations with expected-outcome and lost-points records. Unresolved positions and aborted games are reported rather than guessed or scored as losses.
- Defaults use 90 random surviving midgame/endgame positions (20/21/24/25/28/29 plies) and 20 continuations per agent, with alternating colors and shared openings. These do not measure empty-board opening strength.
- Six-query pilot took 0.86 seconds total; the compiled solver uses an approximately 80 MiB transposition table. No book, GPU, training or paid service is involved.
- Validation before evaluation: 97 tests passed, including ten real-solver endgames independently checked against full-width Python minimax. Normal CI skips only this optional integration check when the executable is absent.

### First exact-reference results
- All 90 initial positions solved and all 100 paired continuations completed without timeout.
- Outcome preservation: random 63/90, minimax 87/90, alpha-beta 89/90, MCTS 90/90, learner 88/90. On the 50 informative positions: 46%, 94%, 98%, 100%, and 96% respectively.
- Continuation W/D/L (20 per agent): random 3/0/17; minimax 9/0/11; alpha-beta 9/1/10; MCTS 10/0/10; learner 9/1/10. Every agent had ten theoretically winnable starts and ten losing starts; MCTS converted all ten wins in this sample.
- This random late-game corpus is largely tactical and contains no drawn starts. Its high accuracy does not establish perfect play or opening strength.
- Added an optional quiet-position filter (no immediate win and at least two moves safe against an immediate loss), using engine checks without solver scores. A second bounded evaluation will use 36 earlier positions at 14–19 plies, seed 92000, with a three-second exact-query timeout and 12 paired continuations per agent. Timeouts and incomplete games will remain explicit.

### Earlier quiet-position results and final validation
- All 36 quiet positions at 14–19 plies solved and all 60 paired continuations completed without timeouts. Solver subprocess time was 14.51 seconds across 322 queries; the initial suite used 9.60 seconds across 223 queries.
- On the 23 informative quiet positions, outcome-preserving decisions: random 8/23 (34.8%), minimax 17/23 (73.9%), alpha-beta 18/23 (78.3%), MCTS 20/23 (87.0%), learner 18/23 (78.3%). Overall preservation on all 36: 58.3%, 83.3%, 86.1%, 91.7%, 86.1%.
- Quiet continuation W/D/L (12 per agent): random 0/0/12; minimax 2/1/9; alpha-beta 4/0/8; MCTS 5/0/7; learner 5/0/7. Each agent had five winning, two drawn and five losing starts under perfect play. MCTS and learner converted the five wins but both dropped the draws.
- These are small midgame/endgame samples with different computational budgets, not Elo ratings, perfect agents or a full empty-board strength measurement. Earlier drawn positions expose failure modes hidden by the first late-game sample.
- Replayed all 160 completed game traces and verified every recorded reference move maximized its exact scores and every actual outcome matched the terminal engine state.
- Final local validation: 98 tests pass on Python 3.13.18, including ten actual solver endgames checked against exhaustive Python minimax; Ruff lint/format and diff checks pass. Normal CI skips only the optional real-solver check because external binaries are not distributed.
- Evaluation results include held-out position labels, full decision/game traces, coverage, stage breakdowns, solver build hashes and unchanged agent/model configuration. Do not use these labels for training. If tuning to these errors, reserve a new held-out seed set.
- No gameplay, learning, model, dependency or Makefile change was made in this follow-up. The external source/binary/license stay in ignored `.solver/`; no opening book, deployment, GPU or paid service was used.

## Application deployment
- Added optional Docker/Gunicorn packaging, non-root execution, a health endpoint and opt-in proxy-prefix support. Existing development Makefile defaults remain unchanged.
- The app deployment script requires an explicit host port, checks the candidate image and supports best-effort rollback for this application only.
- Site-wide content and tooling belong in a separate infrastructure repository. Removed the project homepage, multi-application proxy template/renderer, multi-app checker and site environment example from this repository.
- Public deployment documentation describes only this application's packaging and integration interface. It contains no server inventory or production configuration.
- Preserved the deployment input guard test; all 103 remaining application/game/deployment tests pass. Lint/format, shell syntax and whitespace checks pass. No production changes were made.
