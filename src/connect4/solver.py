"""Evaluation-only subprocess adapter for Pascal Pons's exact solver.

No gameplay, agent or training module imports this adapter. Source and opening
books are not bundled; build the optional executable with scripts/setup_solver.py.
"""

import hashlib
import json
import math
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from connect4.engine import Game

DEFAULT_BINARY = Path(".solver/c4solver")


class SolverError(RuntimeError):
    """The external solver failed or violated its analysis protocol."""


class SolverTimeout(SolverError):
    """No exact answer was obtained within the per-position time budget."""


def replay(moves):
    game = Game()
    for move in moves:
        game = game.play(move)
    return game


def outcome(score):
    """Win/draw/loss from the player-to-move perspective."""
    return (score > 0) - (score < 0)


@dataclass(frozen=True)
class Analysis:
    scores: tuple[int | None, ...]

    @property
    def best_score(self):
        return max(score for score in self.scores if score is not None)

    @property
    def best_moves(self):
        return tuple(
            c for c, score in enumerate(self.scores) if score == self.best_score
        )

    def choose(self):
        # Deterministic tie-breaking, without weakening perfect play.
        return next(c for c in (3, 2, 4, 1, 5, 0, 6) if c in self.best_moves)


def parse_analysis(output, moves, game):
    sequence = "".join(str(c + 1) for c in moves)
    lines = output.splitlines()
    if len(lines) != 1 or not lines[0].startswith(sequence + " "):
        raise SolverError("Solver did not echo exactly one requested position.")
    try:
        raw = [int(value) for value in lines[0][len(sequence) :].split()]
    except ValueError as exc:
        raise SolverError("Solver returned a non-integer score.") from exc
    if len(raw) != 7:
        raise SolverError("Expected seven per-column exact scores.")
    legal = game.legal_moves()
    for column, score in enumerate(raw):
        if column in legal:
            if not -21 <= score <= 21:
                raise SolverError("Solver returned an invalid score for a legal move.")
        elif score != -1000:
            raise SolverError("Solver disagreed about an unavailable column.")
    return Analysis(tuple(None if value == -1000 else value for value in raw))


class ExactSolver:
    def __init__(self, binary=DEFAULT_BINARY, timeout=3.0):
        self.binary = Path(binary).resolve()
        if not self.binary.is_file():
            raise FileNotFoundError(
                "Solver missing: run python scripts/setup_solver.py"
            )
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Solver timeout must be finite and positive.")
        self.timeout = timeout
        self.cache = {}
        self.queries = self.cache_hits = self.timeouts = 0
        self.seconds = 0.0

    def analyze(self, moves):
        moves = tuple(moves)
        game = replay(moves)
        if game.terminal:
            raise ValueError("Exact analysis requires a nonterminal position.")
        if moves in self.cache:
            self.cache_hits += 1
            return self.cache[moves]
        self.queries += 1
        sequence = "".join(str(c + 1) for c in moves)
        start = time.perf_counter()
        try:
            # Empty -b explicitly disables opening-book loading, regardless of cwd.
            result = subprocess.run(
                [str(self.binary), "-a", "-b", ""],
                input=sequence + "\n",
                text=True,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self.timeouts += 1
            raise SolverTimeout(
                f"Exact analysis timed out after {self.timeout}s."
            ) from exc
        except OSError as exc:
            raise SolverError(f"Could not execute solver: {exc}") from exc
        finally:
            self.seconds += time.perf_counter() - start
        if result.returncode:
            raise SolverError(
                f"Solver exited with status {result.returncode}: {result.stderr[:500]}"
            )
        analysis = parse_analysis(result.stdout, moves, game)
        self.cache[moves] = analysis
        return analysis

    def provenance(self):
        digest = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        manifest_path = self.binary.parent / "manifest.json"
        manifest = None
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("binary_sha256") != digest:
                raise SolverError("Solver binary does not match its build manifest.")
        return dict(
            binary=self.binary.name,
            binary_sha256=digest,
            build=manifest,
            opening_book=None,
            exact=True,
            timeout_seconds=self.timeout,
            queries=self.queries,
            cache_hits=self.cache_hits,
            timeouts=self.timeouts,
            subprocess_seconds=self.seconds,
        )
