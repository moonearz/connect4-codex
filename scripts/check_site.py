"""Smoke-check the project homepage and application routes after deployment."""

import argparse
import json
import urllib.parse
import urllib.request


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def inspect_site(base):
    base = base.rstrip("/")

    def request(path, data=None, content_type=None):
        headers = {"Content-Type": content_type} if content_type else {}
        req = urllib.request.Request(base + path, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.geturl(), response.read().decode()

    _, homepage = request("/")
    for app in ("tictactoe", "wordle", "connect4"):
        check(f'href="/{app}/"' in homepage, f"Homepage is missing /{app}/.")
    for app, asset in [("wordle", "script.js"), ("connect4", "app.js")]:
        url, page = request("/" + app)
        check(url == f"{base}/{app}/", f"Unexpected {app} redirect: {url}")
        check(f"/{app}/static/" in page, f"{app} asset URLs lost their prefix.")
        request(f"/{app}/static/{asset}")
    _, page = request("/connect4/")
    check(
        'data-game-url="/connect4/api/game"' in page,
        "Connect Four API URL lost prefix.",
    )
    for seat in (0, 1):
        for difficulty in ("easy", "medium", "hard", "mcts", "learned"):
            moves = [3] if seat == 0 else []
            payload = json.dumps(
                dict(
                    mode="computer",
                    human_player=seat,
                    difficulty=difficulty,
                    moves=moves,
                )
            ).encode()
            _, body = request("/connect4/api/game", payload, "application/json")
            state = json.loads(body)
            check(
                state["turn"] == seat and len(state["moves"]) == len(moves) + 1,
                f"Computer reply failed for seat {seat}, difficulty {difficulty}.",
            )
    url, _ = request("/tictactoe/")
    path = urllib.parse.urlparse(url).path
    check(
        path.startswith("/tictactoe/") and path != "/tictactoe/",
        f"Tic-tac-toe did not launch a game: {url}",
    )
    check("/tictactoe/tictactoe/" not in path, "Duplicated tic-tac-toe prefix.")
    request(
        path + "/move",
        urllib.parse.urlencode({"position": 0}).encode(),
        "application/x-www-form-urlencoded",
    )
    request(
        path + "/new-game",
        urllib.parse.urlencode({"human_player": "O"}).encode(),
        "application/x-www-form-urlencoded",
    )
    expired_url, _ = request("/tictactoe/nonexistent")
    check(
        expired_url.startswith(base + "/tictactoe/")
        and expired_url != base + "/tictactoe/nonexistent",
        "Expired game did not relaunch.",
    )
    _, body = request("/wordle/guess", b'{"history":[]}', "application/json")
    check("answer_guesses" in json.loads(body), "Wordle guess endpoint failed.")
    print(
        "Passed: homepage, app links/assets, both Connect Four seats/all opponents, "
        "Wordle API, and tic-tac-toe launch/move/reset/expired redirects."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", required=True, help="Site root, e.g. https://example.com"
    )
    args = parser.parse_args()
    url = urllib.parse.urlparse(args.base_url)
    if (
        url.scheme not in ("http", "https")
        or not url.netloc
        or url.path not in ("", "/")
    ):
        parser.error("--base-url must be an http(s) site root")
    inspect_site(args.base_url)


if __name__ == "__main__":
    main()
