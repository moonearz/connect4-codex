"""Seeded baselines, depth-limited search, and UCT Monte Carlo search."""

import math
import random
from dataclasses import dataclass, field

from connect4.engine import Game
from connect4.tactics import tactical_moves

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
    def __init__(self, depth=3, pruning=False, evaluator=evaluate, tactical=False):
        if depth < 1:
            raise ValueError("Depth must be positive.")
        self.depth = depth
        self.pruning = pruning
        self.nodes = 0
        self.evaluator = evaluator
        self.tactical = tactical

    def moves(self, game):
        return tactical_moves(game) if self.tactical else ordered(game)

    def value(self, game, depth, alpha, beta):
        self.nodes += 1
        if game.winner is not None:
            return -100000 - depth
        if game.terminal:
            return 0
        if depth == 0:
            return self.evaluator(game)
        best = -math.inf
        for move in self.moves(game):
            score = -self.value(game.play(move), depth - 1, -beta, -alpha)
            best = max(best, score)
            if self.pruning:
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
        return best

    def choose(self, game):
        self.nodes = 0
        moves = self.moves(game)
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
    """UCT with tactical rollouts, bounded value estimates, and subtree reuse."""

    def __init__(self, iterations=600, seed=0, rollout_limit=12):
        if iterations < 1 or rollout_limit < 1:
            raise ValueError("Iterations and rollout limit must be positive.")
        self.iterations = iterations
        self.rollout_limit = rollout_limit
        self.rng = random.Random(seed)
        self.root = None

    def _reuse(self, game):
        if self.root is not None:
            if self.root.game == game:
                return self.root
            # Between this agent's turns, at most one opponent reply follows
            # the move selected at the previous root.
            for child in self.root.children.values():
                if child.game == game:
                    return child
                for reply in child.children.values():
                    if reply.game == game:
                        return reply
        return Node(game)

    def _rollout(self, game):
        start_player = game.turn
        for _ in range(self.rollout_limit):
            if game.terminal:
                break
            moves = tactical_moves(game)
            # Prefer central columns while keeping stochastic exploration.
            move = self.rng.choices(moves, weights=[4 - abs(3 - c) for c in moves])[0]
            game = game.play(move)
        if game.terminal:
            return (
                0.0
                if game.winner is None
                else (1.0 if game.winner == start_player else -1.0)
            )
        value = math.tanh(evaluate(game) / 100)
        return value if game.turn == start_player else -value

    def choose(self, game):
        moves = tactical_moves(game)
        if not moves:
            raise ValueError("Cannot choose a move in a terminal game.")
        if len(moves) == 1 or game.play(moves[0]).winner == game.turn:
            return moves[0]
        root = self._reuse(game)
        self.root = root
        for _ in range(self.iterations):
            node, path = root, [root]
            while not node.game.terminal:
                candidates = tactical_moves(node.game)
                unexplored = [m for m in candidates if m not in node.children]
                if unexplored:
                    move = self.rng.choice(unexplored)
                    child = Node(node.game.play(move))
                    node.children[move] = child
                    node = child
                    path.append(node)
                    break
                node = max(
                    (node.children[m] for m in candidates),
                    key=lambda n: (
                        n.reward / n.visits
                        + 0.7 * math.sqrt(math.log(node.visits) / n.visits)
                    ),
                )
                path.append(node)
            value = self._rollout(node.game)
            for ancestor in path:
                ancestor.visits += 1
                # Each node stores reward for the player who moved into it.
                signed = value if ancestor.game.turn != node.game.turn else -value
                ancestor.reward += (signed + 1) / 2
        return max(
            moves, key=lambda m: root.children[m].visits if m in root.children else 0
        )


def make_agent(name, seed=0):
    factories = {
        "random": lambda: RandomAgent(seed),
        "minimax": lambda: MinimaxAgent(3),
        "alphabeta": lambda: AlphaBetaAgent(5),
        "mcts": lambda: MCTSAgent(600, seed),
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
