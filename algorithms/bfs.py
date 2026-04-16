# algorithms/bfs.py
import time
from collections import deque
from models.puzzle import GOAL, get_neighbors


def bfs(start, timeout=15.0):
    """
    Breadth-First Search with Time Limit.
    Finds shortest path. Best on simpler puzzle states.
    Returns: (path, nodes_explored, time_taken)
    """
    if start == GOAL:
        return [start], 0, 0.0

    t0 = time.time()
    frontier = deque([start])
    came_from = {start: None}
    nodes = 0

    while frontier:
        # ✅ NEW: Check elapsed time
        elapsed = time.time() - t0
        if elapsed > timeout:
            return None, nodes, elapsed

        state = frontier.popleft()
        nodes += 1
        
        for nb in get_neighbors(state):
            if nb not in came_from:
                came_from[nb] = state
                
                if nb == GOAL:
                    # Path reconstruction
                    path = []
                    cur = nb
                    while cur is not None:
                        path.append(cur)
                        cur = came_from[cur]
                    path.reverse()
                    return path, nodes, time.time() - t0
                
                frontier.append(nb)

    return None, nodes, time.time() - t0