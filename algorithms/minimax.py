# algorithms/minimax.py
import math
from models.tictactoe import check_winner, is_full


def minimax(board, depth, is_maximizing, alpha=-math.inf, beta=math.inf):
    """
    Minimax with Alpha-Beta Pruning.
    AI = 'O' (maximizer), Human = 'X' (minimizer).
    """
    winner = check_winner(board)
    if winner == 'O':
        return 10 - depth
    if winner == 'X':
        return -10 + depth
    if is_full(board):
        return 0

    if is_maximizing:
        best = -math.inf
        for i in range(9):
            if board[i] == '':
                board[i] = 'O'
                best = max(best, minimax(board, depth + 1, False, alpha, beta))
                board[i] = ''
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
        return best
    else:
        best = math.inf
        for i in range(9):
            if board[i] == '':
                board[i] = 'X'
                best = min(best, minimax(board, depth + 1, True, alpha, beta))
                board[i] = ''
                beta = min(beta, best)
                if beta <= alpha:
                    break
        return best


def best_move(board):
    """Return the best move index for AI ('O')."""
    best_val = -math.inf
    move = -1
    for i in range(9):
        if board[i] == '':
            board[i] = 'O'
            val = minimax(board, 0, False)
            board[i] = ''
            if val > best_val:
                best_val = val
                move = i
    return move
