import pytest

from connect4.web import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_page(client):
    assert client.get("/").status_code == 200


def test_friend_game_and_reset(client):
    data = client.post("/api/game", json={"moves": [0, 1, 0], "mode": "human"}).json
    assert data["moves"] == [0, 1, 0]
    assert data["turn"] == 1
    assert client.post("/api/game", json={}).json["moves"] == []


def test_computer_replies(client):
    data = client.post("/api/game", json={"moves": [3], "mode": "computer"}).json
    assert len(data["moves"]) == 2
    assert data["turn"] == 0


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {"moves": [7]},
        {"moves": [True]},
        {"moves": [0] * 7},
        {"mode": "oops"},
        {"difficulty": "oops"},
        {"moves": [0, 1, 0, 1, 0, 1, 0, 2]},
    ],
)
def test_bad_requests(client, data):
    assert client.post("/api/game", json=data).status_code == 400


def test_no_reply_after_human_wins(client):
    moves = [0, 1, 0, 1, 0, 1, 0]
    data = client.post("/api/game", json={"moves": moves, "mode": "computer"}).json
    assert data["winner"] == 0
    assert data["moves"] == moves


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard", "mcts", "learned"])
def test_each_difficulty_produces_valid_reply(client, difficulty):
    response = client.post(
        "/api/game", json={"moves": [3], "mode": "computer", "difficulty": difficulty}
    )
    assert response.status_code == 200
    assert len(response.json["moves"]) == 2
    assert response.json["turn"] == 0


@pytest.mark.parametrize("human_player", [0, 1])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard", "mcts", "learned"])
def test_both_seats_open_reply_and_reset(client, human_player, difficulty):
    settings = {
        "mode": "computer",
        "human_player": human_player,
        "difficulty": difficulty,
    }
    start = client.post("/api/game", json=settings).json
    assert start["human_player"] == human_player
    assert start["turn"] == human_player
    assert len(start["moves"]) == human_player
    next_moves = start["moves"] + [start["legal"][0]]
    reply = client.post("/api/game", json={**settings, "moves": next_moves}).json
    assert reply["turn"] == human_player
    assert len(reply["moves"]) == len(next_moves) + 1
    reset = client.post("/api/game", json=settings).json
    assert len(reset["moves"]) == human_player


@pytest.mark.parametrize("human_player", [True, "1", -1, 2, None, [], 1.0])
def test_invalid_seat(client, human_player):
    assert (
        client.post("/api/game", json={"human_player": human_player}).status_code == 400
    )


def test_friend_mode_has_no_automatic_opening(client):
    data = client.post("/api/game", json={"mode": "human", "human_player": 1}).json
    assert data["moves"] == []
    assert data["turn"] == 0


def test_no_computer_reply_after_second_player_wins(client):
    moves = [0, 1, 0, 1, 2, 1, 2, 1]
    data = client.post(
        "/api/game", json={"moves": moves, "mode": "computer", "human_player": 1}
    ).json
    assert data["moves"] == moves
    assert data["winner"] == 1
