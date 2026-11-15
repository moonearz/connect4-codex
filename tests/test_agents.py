import pytest

from connect4.agents import AlphaBetaAgent, MCTSAgent, MinimaxAgent, RandomAgent
from connect4.benchmark import benchmark
from connect4.engine import Game, simulate


def position(moves):
    game = Game()
    for move in moves:
        game = game.play(move)
    return game


@pytest.mark.parametrize("agent", [MinimaxAgent(), AlphaBetaAgent(3), MCTSAgent(80)])
def test_immediate_win(agent):
    assert agent.choose(position([0, 6, 1, 6, 2, 5])) == 3


@pytest.mark.parametrize("agent", [MinimaxAgent(), AlphaBetaAgent(3)])
def test_blocks_loss(agent):
    assert agent.choose(position([6, 0, 6, 1, 5, 2])) == 3


def test_alpha_beta_equivalent_and_prunes():
    game = position([3, 2, 4, 3])
    plain, pruned = MinimaxAgent(4), AlphaBetaAgent(4)
    assert plain.choose(game) == pruned.choose(game)
    assert pruned.nodes < plain.nodes


def test_seeded_agents_reproduce_moves():
    for cls in (RandomAgent, MCTSAgent):
        a, b = cls(seed=34), cls(seed=34)
        game = position([3, 2, 4])
        assert a.choose(game) == b.choose(game)


def test_simulation_and_benchmark():
    assert simulate(RandomAgent(1), RandomAgent(2)).terminal
    result = benchmark("random", "random", 4, 12)
    assert sum(result["wins"]) + result["draws"] == 4
    assert [r["seats"] for r in result["records"]] == [(0, 1), (1, 0)] * 2
    repeated = benchmark("random", "random", 4, 12)
    assert [r["winner"] for r in result["records"]] == [
        r["winner"] for r in repeated["records"]
    ]
    with pytest.raises(ValueError):
        benchmark("random", "random", 3)


def test_paired_random_openings_are_shared_and_reproducible():
    result = benchmark("random", "random", 4, 56, opening_plies=4)
    openings = [r["opening_moves"] for r in result["records"]]
    assert openings[0] == openings[1]
    assert openings[2] == openings[3]
    assert openings[0] != openings[2]
    with pytest.raises(ValueError):
        benchmark("random", "random", opening_plies=7)


def test_benchmark_move_trace_replays_and_includes_opening():
    result = benchmark("random", "random", 2, 12, opening_plies=4)
    for record in result["records"]:
        game = position(record["played_moves"])
        assert game.terminal
        winner = None if game.winner is None else record["seats"][game.winner]
        assert winner == record["winner"]
        assert record["moves"] == len(record["played_moves"])
        assert record["moves"] == sum(record["decisions"]) + 4


@pytest.mark.parametrize("agent", [MCTSAgent(1), MCTSAgent(30)])
def test_mcts_blocks_immediate_loss_even_at_small_budget(agent):
    assert agent.choose(position([6, 0, 6, 1, 5, 2])) == 3


def test_tactical_filter_matches_brute_force():
    import random

    from connect4.tactics import tactical_moves, winning_spots

    rng = random.Random(134)
    for _ in range(150):
        game = Game()
        while not game.terminal:
            occupied = game.bits[0] | game.bits[1]
            spots = winning_spots(game.bits[game.turn], occupied)
            legal = game.legal_moves()
            wins = {m for m in legal if game.play(m).winner == game.turn}
            predicted = {m for m in legal if spots & (1 << (m * 7 + game.heights[m]))}
            assert predicted == wins
            safe = {
                m
                for m in legal
                if not any(
                    game.play(m).play(reply).winner == 1 - game.turn
                    for reply in game.play(m).legal_moves()
                )
            }
            expected = wins or safe or set(legal)
            assert set(tactical_moves(game)) == expected
            game = game.play(rng.choice(legal))
