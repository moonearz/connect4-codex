"""Seeded baselines, depth-limited search, and UCT Monte Carlo search."""

import math
import random
from dataclasses import dataclass, field

from connect4.engine import Game

ORDER = (3, 2, 4, 1, 5, 0, 6)
WINDOWS = []
for r in range(6):
    for c in range(7):
        for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
            cells = [(r + i * dr, c + i * dc) for i in range(4)]
            if all(0 <= y < 6 and 0 <= x < 7 for y, x in cells):
                WINDOWS.append(sum(1 << (x * 7 + y) for y, x in cells))


def ordered(game):
    legal = game.legal_moves()
    return [c for c in ORDER if c in legal]


def evaluate(game):
    own, other = game.bits[game.turn], game.bits[1 - game.turn]
    score = 0
    weights = (0, 1, 8, 64, 4096)
    for window in WINDOWS:
        a, b = (own & window).bit_count(), (other & window).bit_count()
        if not b:
            score += weights[a]
        if not a:
            score -= weights[b]
    return score


class RandomAgent:
    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def choose(self, game):
        return self.rng.choice(game.legal_moves())


class MinimaxAgent:
    def __init__(self, depth=3, pruning=False):
        if depth < 1:
            raise ValueError("Depth must be positive.")
        self.depth = depth
        self.pruning = pruning
        self.nodes = 0

    def value(self, game, depth, alpha, beta):
        self.nodes += 1
        if game.winner is not None:
            return -100000 - depth
        if game.terminal:
            return 0
        if depth == 0:
            return evaluate(game)
        best = -math.inf
        for move in ordered(game):
            score = -self.value(game.play(move), depth - 1, -beta, -alpha)
            best = max(best, score)
            if self.pruning:
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
        return best

    def choose(self, game):
        self.nodes = 0
        moves = ordered(game)
        if not moves:
            raise ValueError("Cannot choose a move in a terminal game.")
        best, choice, alpha = -math.inf, moves[0], -math.inf
        for move in moves:
            score = -self.value(
                game.play(move),
                self.depth - 1,
                -math.inf,
                -alpha if self.pruning else math.inf,
            )
            if score > best:
                best, choice = score, move
            if self.pruning:
                alpha = max(alpha, score)
        return choice


class AlphaBetaAgent(MinimaxAgent):
    def __init__(self, depth=5):
        super().__init__(depth, pruning=True)


@dataclass
class Node:
    game: Game
    visits: int = 0
    reward: float = 0
    children: dict[int, "Node"] = field(default_factory=dict)


class MCTSAgent:
    def __init__(self, iterations=300, seed=0):
        if iterations < 1:
            raise ValueError("Iterations must be positive.")
        self.iterations = iterations
        self.rng = random.Random(seed)

    def choose(self, game):
        moves = ordered(game)
        if not moves:
            raise ValueError("Cannot choose a move in a terminal game.")
        # Always take an immediate win, even with a small rollout budget.
        for move in moves:
            if game.play(move).winner == game.turn:
                return move
        root = Node(game)
        for _ in range(self.iterations):
            node, path = root, [root]
            while not node.game.terminal:
                unexplored = [
                    m for m in node.game.legal_moves() if m not in node.children
                ]
                if unexplored:
                    move = self.rng.choice(unexplored)
                    child = Node(node.game.play(move))
                    node.children[move] = child
                    node = child
                    path.append(node)
                    break
                node = max(
                    node.children.values(),
                    key=lambda n: (
                        n.reward / n.visits
                        + math.sqrt(2 * math.log(node.visits) / n.visits)
                    ),
                )
                path.append(node)
            rollout = node.game
            while not rollout.terminal:
                rollout = rollout.play(self.rng.choice(rollout.legal_moves()))
            for ancestor in path:
                ancestor.visits += 1
                # Reward the player who moved into this node.
                ancestor.reward += (
                    0.5
                    if rollout.winner is None
                    else float(rollout.winner == 1 - ancestor.game.turn)
                )
        return max(root.children, key=lambda m: root.children[m].visits)


def make_agent(name, seed=0):
    factories = {
        "random": lambda: RandomAgent(seed),
        "minimax": lambda: MinimaxAgent(3),
        "alphabeta": lambda: AlphaBetaAgent(5),
        "mcts": lambda: MCTSAgent(300, seed),
    }
    if name in ("learned", "untrained"):
        from connect4.learning import LearningAgent

        return (
            LearningAgent.load(seed=seed)
            if name == "learned"
            else LearningAgent(seed=seed)
        )
    if name not in factories:
        raise ValueError(f"Unknown agent: {name}")
    return factories[name]()
