# algorithms/dfs.py
import time
from models.puzzle import GOAL, get_neighbors

DEPTH_LIMIT = 40

def dfs(start, timeout=15.0):
    """
    Depth-Limited DFS with Time Limit.
    Pure DFS is not suitable for 15-puzzle (infinite loops).
    Uses a depth limit to control exploration and a timeout to ensure responsiveness.
    Returns: (path, nodes_explored, time_taken)
    """
    if start == GOAL:
        return [start], 0, 0.0

    t0 = time.time()
    nodes = 0
    stack = [(start, [start], 0)]
    best_depth = {}

    while stack:
        # ✅ NEW: Check elapsed time
        elapsed = time.time() - t0
        if elapsed > timeout:
            return None, nodes, elapsed

        state, path, depth = stack.pop()
        nodes += 1

        if state == GOAL:
            return path, nodes, time.time() - t0

        if depth >= DEPTH_LIMIT:
            continue

        if state in best_depth and best_depth[state] <= depth:
            continue
        best_depth[state] = depth

        for nb in get_neighbors(state):
            # Check if neighbor is a better path than seen before
            if nb not in best_depth or best_depth[nb] > depth + 1:
                stack.append((nb, path + [nb], depth + 1))

    return None, nodes, time.time() - t0