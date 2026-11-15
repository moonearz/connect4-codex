import pytest

from connect4.engine import Game
from connect4.learning import LearningAgent, features, train


def test_terminal_reward_updates_value():
    game = Game()
    for move in [0, 6, 1, 6, 2, 5]:
        game = game.play(move)
    agent = LearningAgent()
    before = agent.value(game)
    agent.update(game, game.play(3))
    assert agent.value(game) > before
    assert agent.choose(game) == 3


def test_training_reproducible_and_changes_weights(tmp_path):
    a, metadata = train(40, 99)
    b, _ = train(40, 99)
    assert a.weights == b.weights
    assert any(w != 0 for w in a.weights)
    assert sum(metadata["outcomes"]) == 40
    path = tmp_path / "agent.json"
    a.save(path, metadata)
    assert LearningAgent.load(path).weights == a.weights


def test_feature_symmetry():
    game, mirror = Game(), Game()
    for move in [0, 2, 3, 4, 1]:
        game = game.play(move)
        mirror = mirror.play(6 - move)
    assert features(game) == features(mirror)


def test_invalid_model_and_budget():
    with pytest.raises(ValueError):
        LearningAgent([float("nan")] * 8)
    with pytest.raises(ValueError):
        train(0)


def test_learning_search_blocks_immediate_loss():
    game = Game()
    for move in [6, 0, 6, 1, 5, 2]:
        game = game.play(move)
    assert LearningAgent(depth=3).choose(game) == 3


def test_legacy_model_loads_and_trace_signs_alternate(tmp_path):
    import json

    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps({"schema": 1, "algorithm": "linear-tanh-td0", "weights": [0.0] * 8})
    )
    legacy = LearningAgent.load(path, depth=1)
    assert legacy.feature_version == 1
    assert legacy.value(Game()) == 0
    agent = LearningAgent(depth=1)
    traces = [0.0] * 14
    game = Game()
    agent.update(game, game.play(3), traces=traces)
    assert traces[7] == 1
    game = game.play(3)
    agent.update(game, game.play(2), traces=traces)
    assert traces[7] == pytest.approx(0.3)
