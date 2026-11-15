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
