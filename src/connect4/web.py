"""Stateless web API: replay moves to validate every submitted position."""

import os
from secrets import randbits

from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from connect4.agents import make_agent
from connect4.engine import Game


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4096
    if os.environ.get("CONNECT4_BEHIND_PROXY") == "1":
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=0, x_proto=1, x_host=0, x_port=0, x_prefix=1
        )

    @app.get("/healthz")
    def health():
        return jsonify(status="ok")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/game")
    def game_state():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send a JSON object."), 400
        moves = data.get("moves", [])
        mode = data.get("mode", "human")
        difficulty = data.get("difficulty", "easy")
        human_player = data.get("human_player", 0)
        if (
            type(human_player) is not int
            or human_player not in (0, 1)
            or not isinstance(moves, list)
            or len(moves) > 42
            or mode not in ("human", "computer")
            or difficulty not in ("easy", "medium", "hard", "mcts", "learned")
        ):
            return jsonify(error="Invalid game settings."), 400
        game = Game()
        try:
            for move in moves:
                game = game.play(move)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        moves = moves.copy()
        if mode == "computer" and game.turn != human_player and not game.terminal:
            names = {
                "easy": "random",
                "medium": "minimax",
                "hard": "alphabeta",
                "mcts": "mcts",
                "learned": "learned",
            }
            move = make_agent(names[difficulty], seed=randbits(64)).choose(game)
            game = game.play(move)
            moves.append(move)
        return jsonify(
            board=game.board(),
            mode=mode,
            human_player=human_player,
            moves=moves,
            turn=game.turn,
            winner=game.winner,
            terminal=game.terminal,
            legal=list(game.legal_moves()),
        )

    return app
