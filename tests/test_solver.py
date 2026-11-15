import json
import sys
from pathlib import Path

import pytest

from connect4.solver import (
    Analysis,
    ExactSolver,
    SolverError,
    SolverTimeout,
    parse_analysis,
    replay,
)
from connect4.solver_benchmark import (
    decision_record,
    evaluate_decisions,
    evaluate_games,
    generate_positions,
    summarize_decisions,
)


@pytest.fixture
def fake_binary(tmp_path):
    def create(body):
        binary = tmp_path / "fake solver"
        binary.write_text(f"#!{sys.executable}\nimport sys\n{body}\n")
        binary.chmod(0o755)
        return binary

    return create


def test_adapter_encodes_columns_and_caches(fake_binary):
    binary = fake_binary(
        "line = sys.stdin.readline().rstrip('\\n')\n"
        "assert line == '147'\n"
        "print(line + ' 1 2 0 -1 -2 3 4')"
    )
    solver = ExactSolver(binary)
    analysis = solver.analyze([0, 3, 6])
    assert analysis.scores == (1, 2, 0, -1, -2, 3, 4)
    assert analysis.choose() == 6
    assert solver.analyze([0, 3, 6]) is analysis
    assert solver.queries == solver.cache_hits == 1
    assert solver.provenance()["opening_book"] is None


def test_empty_sequence_is_supported(fake_binary):
    binary = fake_binary(
        "assert sys.stdin.readline() == '\\n'\nprint(' 0 0 0 1 0 0 0')"
    )
    assert ExactSolver(binary).analyze([]).choose() == 3


@pytest.mark.parametrize("moves", [[True], [7], [0] * 7, [0, 1, 0, 1, 0, 1, 0]])
def test_invalid_or_terminal_positions_never_reach_process(fake_binary, moves):
    solver = ExactSolver(fake_binary("raise AssertionError('must not execute')"))
    with pytest.raises(ValueError):
        solver.analyze(moves)
    assert solver.queries == 0


@pytest.mark.parametrize(
    "text",
    [
        "wrong 0 0 0 0 0 0 0",
        "1 0 0",
        "1 a 0 0 0 0 0 0",
        "1 -1000 0 0 0 0 0 0",
        "1 22 0 0 0 0 0 0",
        "1 0 0 0 0 0 0 0\nextra",
    ],
)
def test_bad_protocol_is_rejected(text):
    with pytest.raises(SolverError):
        parse_analysis(text, [0], replay([0]))


def test_full_column_encoding():
    moves = [0] * 6
    game = replay(moves)
    analysis = parse_analysis("111111 -1000 1 0 -1 0 1 0", moves, game)
    assert analysis.scores[0] is None
    with pytest.raises(SolverError):
        parse_analysis("111111 0 1 0 -1 0 1 0", moves, game)


def test_timeouts_and_process_failure_are_not_answers(fake_binary):
    solver = ExactSolver(fake_binary("import time\ntime.sleep(2)"), timeout=0.05)
    with pytest.raises(SolverTimeout):
        solver.analyze([0])
    assert solver.timeouts == 1
    assert not solver.cache
    solver = ExactSolver(fake_binary("sys.stderr.write('failed'); sys.exit(4)"))
    with pytest.raises(SolverError, match="status 4"):
        solver.analyze([0])


def test_binary_manifest_mismatch_fails(fake_binary):
    binary = fake_binary("print(' 0 0 0 0 0 0 0')")
    (binary.parent / "manifest.json").write_text(json.dumps({"binary_sha256": "wrong"}))
    with pytest.raises(SolverError, match="manifest"):
        ExactSolver(binary).provenance()


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout(fake_binary, timeout):
    with pytest.raises(ValueError):
        ExactSolver(fake_binary("pass"), timeout)


def test_regret_separates_speed_from_outcome():
    analysis = Analysis((3, 2, 0, -1, -2, -3, -4))
    slower_win = decision_record(analysis, 1)
    assert slower_win["outcome_preserved"]
    assert not slower_win["exact_optimal"]
    assert slower_win["score_regret"] == 1
    assert slower_win["outcome_regret"] == 0
    assert decision_record(analysis, 2)["transition"] == "win_to_draw"
    assert decision_record(analysis, 3)["transition"] == "win_to_loss"
    draw = Analysis((0, -1, -1, -1, -1, -1, -1))
    assert decision_record(draw, 1)["transition"] == "draw_to_loss"
    lost = decision_record(Analysis((-1, -2, -3, -4, -5, -6, -7)), 6)
    assert lost["outcome_preserved"] and not lost["informative"]
    stats = summarize_decisions([dict(seconds=0.1, **r) for r in [slower_win, lost]])
    assert stats["informative_positions"] == 1
    assert stats["informative_preservation_rate"] == 1
    assert summarize_decisions([])["outcome_preservation_rate"] is None
    with pytest.raises(ValueError):
        decision_record(analysis, True)


def test_corpus_is_seeded_balanced_legal_and_unique():
    positions = generate_positions(12, 77)
    assert positions == generate_positions(12, 77)
    assert [p["turn"] for p in positions] == [0, 1] * 6
    games = [replay(p["moves"]) for p in positions]
    assert all(not g.terminal and len(g.legal_moves()) >= 2 for g in games)
    assert len({g.bits for g in games}) == 12
    with pytest.raises(ValueError):
        generate_positions(0)
    with pytest.raises(ValueError):
        generate_positions(1, plies=(42,))


def brute_value(game):
    """Independent full-width endgame minimax using the documented score units."""
    if game.winner is not None:
        return -((44 - sum(game.heights)) // 2)
    if game.terminal:
        return 0
    return max(-brute_value(game.play(c)) for c in game.legal_moves())


class BruteOracle:
    def analyze(self, moves):
        game = replay(moves)
        return Analysis(
            tuple(
                -brute_value(game.play(c)) if c in game.legal_moves() else None
                for c in range(7)
            )
        )


def test_paired_continuations_replay_and_respect_perfect_bound():
    positions = generate_positions(2, 387, plies=(36, 37))
    oracle = BruteOracle()
    analyses = {p["id"]: oracle.analyze(p["moves"]) for p in positions}
    result = evaluate_games("random", positions, analyses, oracle, games=4)
    assert result["summary"]["completed"] == 4
    assert [r["agent_player"] for r in result["games"]] == [0, 1, 0, 1]
    for record in result["games"]:
        assert replay(record["played_moves"]).terminal
        assert record["points_lost"] >= 0
        for decision in record["oracle_decisions"]:
            assert decision["scores"][decision["move"]] == max(
                s for s in decision["scores"] if s is not None
            )
    with pytest.raises(ValueError):
        evaluate_games("random", positions, analyses, oracle, games=3)


def test_unresolved_positions_are_excluded_for_all_agents():
    positions = generate_positions(2, 65, plies=(36, 37))
    analyses = {0: BruteOracle().analyze(positions[0]["moves"])}
    for name in ("random", "alphabeta"):
        result = evaluate_decisions(name, positions, analyses)
        assert [r["position_id"] for r in result["decisions"]] == [0]

    class TimeoutOracle:
        def analyze(self, moves):
            raise SolverTimeout("test timeout")

    result = evaluate_games("random", positions, analyses, TimeoutOracle(), games=4)
    assert result["summary"]["aborted"] == 4
    assert result["summary"]["completed"] == 0
    assert result["summary"]["losses"] == result["summary"]["draws"] == 0


def test_real_solver_matches_full_endgame_search():
    binary = Path(".solver/c4solver")
    if not binary.exists():
        pytest.skip("Optional integration: build with scripts/setup_solver.py")
    solver = ExactSolver(binary)
    positions = generate_positions(10, 221, plies=(36, 37, 38, 39))
    for position in positions:
        moves = position["moves"]
        assert solver.analyze(moves) == BruteOracle().analyze(moves)


def test_draw_is_not_scored_as_a_loss():
    moves = [
        3,
        1,
        0,
        5,
        1,
        3,
        3,
        4,
        1,
        3,
        1,
        1,
        5,
        4,
        0,
        5,
        3,
        4,
        1,
        3,
        5,
        5,
        5,
        6,
        4,
        0,
        6,
        6,
        4,
        2,
        4,
        2,
        2,
        0,
        0,
        6,
        6,
        2,
        0,
        6,
        2,
        2,
    ]
    position = dict(id=0, moves=moves[:-1])
    oracle = BruteOracle()
    result = evaluate_games(
        "random", [position], {0: oracle.analyze(position["moves"])}, oracle, games=2
    )
    assert result["summary"]["draws"] == 2
