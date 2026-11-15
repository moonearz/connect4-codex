"""Stateless web API: replay moves to validate every submitted position."""

import random

from flask import Flask, jsonify, render_template, request

from connect4.engine import Game


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4096

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
        if (
            not isinstance(moves, list)
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
        if mode == "computer" and game.turn == 1 and not game.terminal:
            move = random.choice(game.legal_moves())
            game = game.play(move)
            moves.append(move)
        return jsonify(
            board=game.board(),
            moves=moves,
            turn=game.turn,
            winner=game.winner,
            terminal=game.terminal,
            legal=list(game.legal_moves()),
        )

    return app
