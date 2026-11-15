"""Bitboard tactical checks shared by search and rollouts."""

from connect4.engine import Game

ORDER = (3, 2, 4, 1, 5, 0, 6)
BOARD_MASK = sum(((1 << 6) - 1) << (c * 7) for c in range(7))


def winning_spots(board: int, occupied: int) -> int:
    """Empty cells completing four; includes cells not yet supported by gravity."""
    spots = 0
    for d in (1, 7, 6, 8):
        spots |= (board << d) & (board << (2 * d)) & (board << (3 * d))
        spots |= (board >> d) & (board >> (2 * d)) & (board >> (3 * d))
        spots |= (board << d) & (board << (2 * d)) & (board >> d)
        spots |= (board >> d) & (board >> (2 * d)) & (board << d)
    return spots & BOARD_MASK & ~occupied


def tactical_moves(game: Game) -> list[int]:
    """Take wins, block forced threats, and avoid enabling an immediate loss.

    If every move loses immediately, return all legal moves rather than an empty
    list. No legal continuation is incorrectly treated as a terminal state.
    """
    moves = [c for c in ORDER if c in game.legal_moves()]
    occupied = game.bits[0] | game.bits[1]
    own = winning_spots(game.bits[game.turn], occupied)
    other = winning_spots(game.bits[1 - game.turn], occupied)
    landing = {c: 1 << (c * 7 + game.heights[c]) for c in moves}
    wins = [c for c in moves if landing[c] & own]
    if wins:
        return wins
    threats = [c for c in moves if landing[c] & other]
    if len(threats) > 1:
        return moves
    candidates = threats or moves
    safe = [c for c in candidates if not ((landing[c] << 1) & other)]
    return safe or moves
