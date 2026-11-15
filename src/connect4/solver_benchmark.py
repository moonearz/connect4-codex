"""Evaluate move quality and paired game continuations against an exact solver."""

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

from connect4.agents import make_agent
from connect4.benchmark import add_provenance
from connect4.engine import Game
from connect4.solver import (
    DEFAULT_BINARY,
    ExactSolver,
    SolverError,
    SolverTimeout,
    replay,
)
from connect4.solver import outcome as sign

DEFAULT_PLIES = (20, 21, 24, 25, 28, 29)
NAMES = {-1: "loss", 0: "draw", 1: "win"}


def generate_positions(count=90, seed=90000, plies=DEFAULT_PLIES, quiet=False):
    """Reject terminal random games; never select positions by solver outcome."""
    if (
        count < 1
        or not plies
        or any(type(p) is not int or not 0 <= p <= 40 for p in plies)
    ):
        raise ValueError("Use a positive position count and plies between 0 and 40.")
    rng, positions, seen = random.Random(seed), [], set()
    attempts = 0
    while len(positions) < count:
        attempts += 1
        if attempts > max(10000, count * 2000):
            raise ValueError(
                "Could not generate enough distinct nonterminal positions."
            )
        target = plies[len(positions) % len(plies)]
        game, moves = Game(), []
        while not game.terminal and len(moves) < target:
            move = rng.choice(game.legal_moves())
            moves.append(move)
            game = game.play(move)
        if game.terminal or len(game.legal_moves()) < 2 or game.bits in seen:
            continue
        if quiet:
            children = [game.play(c) for c in game.legal_moves()]
            if any(child.winner == game.turn for child in children):
                continue
            safe = sum(
                not any(
                    child.play(reply).winner == child.turn
                    for reply in child.legal_moves()
                )
                for child in children
            )
            if safe < 2:
                continue
        seen.add(game.bits)
        positions.append(
            dict(id=len(positions), moves=moves, ply=target, turn=game.turn)
        )
    return positions


def decision_record(analysis, move):
    if type(move) is not int or not 0 <= move < 7 or analysis.scores[move] is None:
        raise ValueError("Agent selected an illegal move.")
    best, selected = analysis.best_score, analysis.scores[move]
    best_outcome, selected_outcome = sign(best), sign(selected)
    outcomes = {sign(score) for score in analysis.scores if score is not None}
    return dict(
        move=move,
        best_score=best,
        selected_score=selected,
        exact_optimal=selected == best,
        outcome_preserved=best_outcome == selected_outcome,
        informative=len(outcomes) > 1,
        score_regret=best - selected,
        outcome_regret=best_outcome - selected_outcome,
        transition=f"{NAMES[best_outcome]}_to_{NAMES[selected_outcome]}",
    )


def summarize_decisions(records):
    n = len(records)
    informative = [r for r in records if r["informative"]]
    return dict(
        positions=n,
        exact_optimal_rate=sum(r["exact_optimal"] for r in records) / n if n else None,
        outcome_preservation_rate=sum(r["outcome_preserved"] for r in records) / n
        if n
        else None,
        informative_positions=len(informative),
        informative_preservation_rate=(
            sum(r["outcome_preserved"] for r in informative) / len(informative)
            if informative
            else None
        ),
        mean_score_regret=sum(r["score_regret"] for r in records) / n if n else None,
        transitions=dict(Counter(r["transition"] for r in records)),
        mean_move_seconds=sum(r["seconds"] for r in records) / n if n else None,
    )


def evaluate_decisions(name, positions, analyses, seed=90000, factory=make_agent):
    records = []
    for position in positions:
        analysis = analyses.get(position["id"])
        if analysis is None:
            continue  # Every agent is scored on the same resolved subset.
        agent = factory(name, seed + position["id"])
        game = replay(position["moves"])
        start = time.perf_counter()
        move = agent.choose(game)
        seconds = time.perf_counter() - start
        records.append(
            dict(
                position_id=position["id"],
                ply=sum(game.heights),
                turn=game.turn,
                seconds=seconds,
                **decision_record(analysis, move),
            )
        )
    return dict(
        summary=summarize_decisions(records),
        by_ply={
            str(p): summarize_decisions([r for r in records if r["ply"] == p])
            for p in sorted({r["ply"] for r in records})
        },
        decisions=records,
    )


def play_continuation(
    name, position, analysis, solver, agent_player, seed, factory=make_agent
):
    moves = position["moves"].copy()
    game = replay(moves)
    expected = sign(analysis.best_score) * (1 if agent_player == game.turn else -1)
    agent = factory(name, seed)
    record = dict(
        position_id=position["id"],
        seed=seed,
        agent_player=agent_player,
        agent_starts=agent_player == game.turn,
        expected_outcome=NAMES[expected],
        played_moves=moves,
        oracle_decisions=[],
        agent_seconds=0.0,
        agent_decisions=0,
        status="completed",
    )
    while not game.terminal:
        if game.turn == agent_player:
            start = time.perf_counter()
            move = agent.choose(game)
            record["agent_seconds"] += time.perf_counter() - start
            record["agent_decisions"] += 1
        else:
            try:
                solved = solver.analyze(moves)
            except SolverTimeout as exc:
                record.update(status="timeout", error=str(exc), actual_outcome=None)
                return record
            move = solved.choose()
            record["oracle_decisions"].append(
                dict(ply=len(moves), move=move, scores=solved.scores)
            )
        game = game.play(move)
        moves.append(move)
    actual = 0 if game.winner is None else (1 if game.winner == agent_player else -1)
    if actual > expected:
        raise SolverError(
            "Game exceeded the oracle bound; reference consistency failed."
        )
    record.update(
        actual_outcome=NAMES[actual],
        outcome_preserved=actual == expected,
        winner=game.winner,
        points_lost=(expected - actual) / 2,
    )
    return record


def evaluate_games(
    name, positions, analyses, solver, games=20, seed=90000, factory=make_agent
):
    if games < 0 or games % 2 or games // 2 > len(positions):
        raise ValueError("Use an even game count with at least one position per pair.")
    records = []
    for index in range(games):
        position = positions[index // 2]
        analysis = analyses.get(position["id"])
        player = index % 2
        if analysis is None:
            records.append(
                dict(
                    position_id=position["id"],
                    agent_player=player,
                    status="opening_timeout",
                    actual_outcome=None,
                )
            )
            continue
        records.append(
            play_continuation(
                name, position, analysis, solver, player, seed + index // 2, factory
            )
        )
    completed = [r for r in records if r["status"] == "completed"]
    outcomes = Counter(r["actual_outcome"] for r in completed)
    seconds = sum(r["agent_seconds"] for r in completed)
    decisions = sum(r["agent_decisions"] for r in completed)
    return dict(
        summary=dict(
            requested=games,
            completed=len(completed),
            aborted=games - len(completed),
            wins=outcomes["win"],
            draws=outcomes["draw"],
            losses=outcomes["loss"],
            winnable_starts=sum(r["expected_outcome"] == "win" for r in completed),
            drawable_starts=sum(r["expected_outcome"] == "draw" for r in completed),
            points_lost_from_perfect=sum(r["points_lost"] for r in completed),
            by_seat={
                str(p): dict(
                    Counter(
                        r["actual_outcome"] for r in completed if r["agent_player"] == p
                    )
                )
                for p in (0, 1)
            },
            mean_move_seconds=seconds / decisions if decisions else None,
        ),
        games=records,
    )


def write_report(result, destination):
    def percent(value):
        return "n/a" if value is None else f"{100 * value:.1f}%"

    lines = [
        "# Exact-solver evaluation",
        "",
        "Reference: Pascal Pons Connect4 solver, strong analysis, no opening book.",
        "Move outcomes are from the player-to-move perspective. The corpus was",
        "generated from seeded random legal games, rejecting terminal games and",
        "duplicates. No positions were selected by solver outcome.",
        "",
        "| Agent | Scored | Exact-score optimal | Outcome preserved | "
        "Informative outcome preserved | Continuation W/D/L | Aborted |",
        "|---|---:|---:|---:|---:|---|---:|",
    ]
    for name, metrics in result["results"].items():
        d, g = metrics["move_quality"]["summary"], metrics["continuations"]["summary"]
        lines.append(
            f"| {name} | {d['positions']} | {percent(d['exact_optimal_rate'])} | "
            f"{percent(d['outcome_preservation_rate'])} | "
            f"{percent(d['informative_preservation_rate'])} | "
            f"{g['wins']}/{g['draws']}/{g['losses']} | {g['aborted']} |"
        )
    solved = [p for p in result["positions"] if p.get("status") == "solved"]
    distribution = dict(Counter(p["outcome"] for p in solved))
    informative = next(iter(result["results"].values()))["move_quality"]["summary"][
        "informative_positions"
    ]
    lines += [
        "",
        f"Seed: {result['seed']}; stages (plies): {result['plies']}.",
        f"Coverage: {len(solved)}/{len(result['positions'])} positions solved; "
        f"{informative} informative positions. Starting outcomes: {distribution}.",
    ]
    if result.get("quiet"):
        lines += [
            "",
            "Quiet-position filter: no immediate win and at least two moves",
            "that avoid an immediate opponent win. This uses local tactical",
            "checks only, not solver scores or agent performance.",
        ]
    lines += [
        "",
        "## Reading the results",
        "",
        "- Exact-score optimal means the move has the best solver score, including",
        "  its preference for faster wins and slower losses.",
        "- Outcome preservation accepts any move retaining the best achievable",
        "  win/draw/loss. It does not penalize a slower forced win.",
        "- Informative positions have legal moves with different win/draw/loss",
        "  outcomes. Already-lost positions can inflate the overall preservation",
        "  rate; use this subset and the recorded transitions to assess blunders.",
        "- W/D/L describes complete continuations from sampled midgame positions,",
        "  not games from an empty board. Each opening is played twice, assigning",
        "  the agent to each color. Raw records include each starting position's",
        "  perfect-play outcome and how many attainable points the agent lost.",
        "- Timeouts are unresolved or aborted, never losses, draws or heuristic",
        "  answers. All agents share the same resolved move-quality subset.",
        "- These are small samples, not Elo ratings. Different starting stages and",
        "  outcome distributions can change the ranking. Late positions are easier",
        "  for finite-depth agents; the report does not establish opening strength.",
        "- The oracle is evaluation-only. Agents, training, and the web app do not",
        "  use it or its labels. No opening book or pretrained agent was downloaded.",
        "",
        "See `results.json` for seeds, full positions/scores, decisions, game",
        "traces, timeout counts, build/source/model hashes and computational budgets.",
    ]
    (destination / "RESULTS.md").write_text("\n".join(lines) + "\n")


def save_checkpoint(result, solver, destination):
    result["solver"] = solver.provenance()
    temporary = destination / "results.json.tmp"
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(destination / "results.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument(
        "--agents",
        nargs="+",
        default=["random", "minimax", "alphabeta", "mcts", "learned"],
    )
    parser.add_argument("--positions", type=int, default=90)
    parser.add_argument("--plies", type=int, nargs="+", default=list(DEFAULT_PLIES))
    parser.add_argument(
        "--games",
        type=int,
        default=20,
        help="Even continuations per agent; 0 disables.",
    )
    parser.add_argument("--seed", type=int, default=90000)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reject immediate wins and positions with fewer than two safe moves.",
    )
    parser.add_argument("--output", type=Path, default=Path("experiments/solver"))
    args = parser.parse_args()
    if args.games < 0 or args.games % 2 or args.games // 2 > args.positions:
        parser.error("--games must be even, nonnegative, and at most 2 * --positions")
    solver = ExactSolver(args.binary, args.timeout)
    solver.provenance()  # Fail early if the binary differs from its manifest.
    for name in args.agents:
        make_agent(name, args.seed)  # Validate names before doing expensive work.
    positions = generate_positions(
        args.positions, args.seed, tuple(args.plies), args.quiet
    )
    result = add_provenance(
        dict(
            agents=args.agents,
            seed=args.seed,
            plies=args.plies,
            quiet=args.quiet,
            positions=positions,
            results={},
            status="running",
        )
    )
    args.output.mkdir(parents=True, exist_ok=True)
    analyses = {}
    for index, position in enumerate(positions):
        try:
            analysis = solver.analyze(position["moves"])
            analyses[position["id"]] = analysis
            position.update(
                status="solved",
                scores=analysis.scores,
                outcome=NAMES[sign(analysis.best_score)],
            )
        except SolverTimeout as exc:
            position.update(status="timeout", error=str(exc), scores=None)
        if (index + 1) % 15 == 0:
            save_checkpoint(result, solver, args.output)
            print(f"Analyzed {index + 1}/{len(positions)} positions", flush=True)
    for name in args.agents:
        quality = evaluate_decisions(name, positions, analyses, args.seed)
        games = evaluate_games(name, positions, analyses, solver, args.games, args.seed)
        result["results"][name] = dict(move_quality=quality, continuations=games)
        save_checkpoint(result, solver, args.output)
        print(f"{name}: {quality['summary']}; games: {games['summary']}", flush=True)
    result.update(status="completed", solver=solver.provenance())
    save_checkpoint(result, solver, args.output)
    write_report(result, args.output)


if __name__ == "__main__":
    main()
