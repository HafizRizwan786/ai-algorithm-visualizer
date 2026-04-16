# models/puzzle.py
import random

GOAL = (1, 2, 3, 4,
        5, 6, 7, 8,
        9, 10, 11, 12,
        13, 14, 15, 0)   # 0 = blank


def get_blank(state):
    return state.index(0)


def get_neighbors(state):
    blank = get_blank(state)
    row, col = divmod(blank, 4)
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            nb = nr * 4 + nc
            s = list(state)
            s[blank], s[nb] = s[nb], s[blank]
            neighbors.append(tuple(s))
    return neighbors


def generate_puzzle():
    """
    Generate a random solvable puzzle by making 30 random moves
    from the goal state. Guarantees solvability.
    """
    state = list(GOAL)
    prev_blank = None
    for _ in range(30):
        blank = state.index(0)
        row, col = divmod(blank, 4)
        options = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 4 and 0 <= nc < 4:
                options.append(nr * 4 + nc)
        if prev_blank is not None and len(options) > 1:
            options = [o for o in options if o != prev_blank]
        nb = random.choice(options)
        state[blank], state[nb] = state[nb], state[blank]
        prev_blank = blank
    result = tuple(state)
    return result if result != GOAL else generate_puzzle()


def is_goal(state):
    return state == GOAL
