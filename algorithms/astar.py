# algorithms/astar.py
import heapq
import time
from models.puzzle import GOAL, get_neighbors


def h1_misplaced(state):
    """h1: Number of misplaced tiles (excluding blank)."""
    return sum(1 for i in range(16) if state[i] != 0 and state[i] != GOAL[i])


def h2_manhattan(state):
    """h2: Sum of Manhattan distances to goal position."""
    dist = 0
    for i, val in enumerate(state):
        if val != 0:
            goal_idx = val - 1
            dist += abs(i // 4 - goal_idx // 4) + abs(i % 4 - goal_idx % 4)
    return dist


def astar(start, heuristic='h2'):
    """
    A* Search.
    Always finds optimal solution.
    heuristic: 'h1' = misplaced tiles, 'h2' = Manhattan distance
    Returns: (path, nodes_explored, time_taken)
    """
    hfn = h1_misplaced if heuristic == 'h1' else h2_manhattan

    if start == GOAL:
        return [start], 0, 0.0

    t0 = time.time()
    counter = 0
    heap = [(hfn(start), 0, counter, start)]
    g_cost = {start: 0}
    came_from = {start: None}
    nodes = 0

    while heap:
        f, g, _, state = heapq.heappop(heap)
        nodes += 1

        if state == GOAL:
            path = []
            cur = state
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path, nodes, time.time() - t0

        if g > g_cost.get(state, float('inf')):
            continue

        for nb in get_neighbors(state):
            ng = g + 1
            if ng < g_cost.get(nb, float('inf')):
                g_cost[nb] = ng
                came_from[nb] = state
                counter += 1
                heapq.heappush(heap, (ng + hfn(nb), ng, counter, nb))

    return None, nodes, time.time() - t0
