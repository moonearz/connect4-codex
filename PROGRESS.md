# Development log

## Phase 1
- Implemented immutable sentinel bitboards and a shared agent protocol.
- Added direction, gravity, validation, terminal, and randomized independent grid-oracle tests.
- Python 3.13 installed locally; development environment lives in `.venv`.

## Phase 2
- Added responsive Flask interface with friend/computer modes, reset, keyboard-accessible column controls, and server-side replay validation.
- Added API integration tests covering malformed inputs, terminal games, reset, and computer replies.
- Validation: 25 tests passed; Ruff passed. Difficulty choices will be connected to search agents in Phase 3.
