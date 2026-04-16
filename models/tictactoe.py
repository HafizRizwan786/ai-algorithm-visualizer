# models/tictactoe.py

WINS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # cols
    (0, 4, 8), (2, 4, 6)               # diagonals
]


def check_winner(board):
    """Return 'X', 'O', or None."""
    for a, b, c in WINS:
        if board[a] == board[b] == board[c] and board[a] != '':
            return board[a]
    return None


def get_winning_line(board):
    for combo in WINS:
        a, b, c = combo
        if board[a] == board[b] == board[c] and board[a] != '':
            return list(combo)
    return None


def is_full(board):
    return all(cell != '' for cell in board)


def is_terminal(board):
    return check_winner(board) is not None or is_full(board)
