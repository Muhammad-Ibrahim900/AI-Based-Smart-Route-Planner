# =============================================================================
# algorithms.py — AI Search Algorithms for Route Planning
# =============================================================================
# Implements: BFS, DFS, UCS, A* (main), Greedy Best First Search
#
# Every algorithm returns a SearchResult namedtuple with:
#   path           : list of node names from source to destination
#   total_cost     : total effective cost of the path
#   nodes_explored : number of nodes popped from the frontier
#   time_taken     : seconds elapsed
# =============================================================================

import time
import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from graph import CityGraph
from utils import heuristic, reconstruct_path


# =============================================================================
# Result Container
# =============================================================================

@dataclass
class SearchResult:
    """Holds the outcome of a search algorithm run."""
    algorithm      : str
    path           : list[str]
    total_cost     : float
    nodes_explored : int
    time_taken     : float          # seconds

    def found(self) -> bool:
        return len(self.path) > 0

    def summary(self) -> str:
        if not self.found():
            return f"[{self.algorithm}] No path found."
        return (
            f"[{self.algorithm}]\n"
            f"  Path          : {' -> '.join(self.path)}\n"
            f"  Total Cost    : {self.total_cost:.2f} km\n"
            f"  Nodes Explored: {self.nodes_explored}\n"
            f"  Time Taken    : {self.time_taken*1000:.3f} ms"
        )


# =============================================================================
# 1. Breadth-First Search (BFS)
# =============================================================================
# Strategy    : FIFO queue — explore level by level
# Optimality  : Optimal only for UNWEIGHTED graphs (finds shortest hop-count path)
# Completeness: Complete (will always find a path if one exists)
# Time/Space  : O(b^d) where b = branching factor, d = depth of solution
# NOTE        : BFS ignores edge weights; it treats all edges as cost=1
# =============================================================================

def bfs(graph: CityGraph, source: str, destination: str) -> SearchResult:
    """
    Breadth-First Search.
    Uses edge EXISTENCE (not weights) to find the fewest-hops path.
    """
    start_time = time.perf_counter()
    nodes_explored = 0

    # frontier: deque of (current_node, path_so_far)
    frontier = deque()
    frontier.append((source, [source]))

    # visited set to avoid re-processing nodes
    visited = set()
    visited.add(source)

    while frontier:
        current, path = frontier.popleft()
        nodes_explored += 1

        # ── Goal Test ──
        if current == destination:
            # Compute actual cost of the found path
            cost = _path_cost(graph, path)
            elapsed = time.perf_counter() - start_time
            return SearchResult("BFS", path, cost, nodes_explored, elapsed)

        # ── Expand ──
        for edge in graph.get_neighbors(current):
            neighbor = edge.node_to
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append((neighbor, path + [neighbor]))

    # No path found
    elapsed = time.perf_counter() - start_time
    return SearchResult("BFS", [], 0.0, nodes_explored, elapsed)


# =============================================================================
# 2. Depth-First Search (DFS)
# =============================================================================
# Strategy    : LIFO stack — go deep before exploring siblings
# Optimality  : NOT optimal (may find a longer path)
# Completeness: NOT complete for infinite/cyclic graphs (we use visited to fix)
# Time/Space  : O(b^m) where m = maximum depth
# NOTE        : DFS can find a valid path fast but it won't be the cheapest
# =============================================================================

def dfs(graph: CityGraph, source: str, destination: str) -> SearchResult:
    """
    Depth-First Search (iterative with explicit stack to avoid recursion limit).
    """
    start_time = time.perf_counter()
    nodes_explored = 0

    # frontier: stack of (current_node, path_so_far)
    frontier = [(source, [source])]   # list used as stack
    visited = set()
    visited.add(source)

    while frontier:
        current, path = frontier.pop()   # LIFO
        nodes_explored += 1

        # ── Goal Test ──
        if current == destination:
            cost = _path_cost(graph, path)
            elapsed = time.perf_counter() - start_time
            return SearchResult("DFS", path, cost, nodes_explored, elapsed)

        # ── Expand ──
        for edge in graph.get_neighbors(current):
            neighbor = edge.node_to
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append((neighbor, path + [neighbor]))

    elapsed = time.perf_counter() - start_time
    return SearchResult("DFS", [], 0.0, nodes_explored, elapsed)


# =============================================================================
# 3. Uniform Cost Search (UCS) — Also known as Dijkstra's Algorithm
# =============================================================================
# Strategy    : Priority queue ordered by cumulative path cost g(n)
# Optimality  : OPTIMAL — always finds lowest-cost path
# Completeness: Complete (assuming non-negative costs)
# Time/Space  : O((V + E) log V) with a binary heap
# Key idea    : Expand the cheapest frontier node first
# =============================================================================

def ucs(graph: CityGraph, source: str, destination: str) -> SearchResult:
    """
    Uniform Cost Search — optimal weighted shortest path.
    Priority queue item: (cumulative_cost, node_name, path_list)
    """
    start_time = time.perf_counter()
    nodes_explored = 0

    # (cumulative_cost, tie_breaker, node, path)
    # tie_breaker avoids comparing lists when costs are equal
    counter = 0
    frontier = [(0.0, counter, source, [source])]
    heapq.heapify(frontier)

    # best known cost to reach each node
    cost_so_far: dict[str, float] = {source: 0.0}

    while frontier:
        g, _, current, path = heapq.heappop(frontier)
        nodes_explored += 1

        # ── Goal Test ──
        if current == destination:
            elapsed = time.perf_counter() - start_time
            return SearchResult("UCS", path, g, nodes_explored, elapsed)

        # ── Expand ──
        for edge in graph.get_neighbors(current):
            neighbor    = edge.node_to
            new_cost    = g + edge.effective_cost

            # Only push if we found a cheaper way to reach neighbor
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                counter += 1
                heapq.heappush(frontier,
                               (new_cost, counter, neighbor, path + [neighbor]))

    elapsed = time.perf_counter() - start_time
    return SearchResult("UCS", [], 0.0, nodes_explored, elapsed)


# =============================================================================
# 4. A* Search  ← MAIN ALGORITHM (MANDATORY)
# =============================================================================
# Strategy    : Priority queue ordered by f(n) = g(n) + h(n)
#               g(n) = cost from start to n (exact)
#               h(n) = heuristic estimate from n to goal
# Optimality  : OPTIMAL if h(n) is ADMISSIBLE
# Completeness: Complete
#
# Heuristic used: Euclidean straight-line distance (see utils.py)
#   Admissible  : h(n) never OVERESTIMATES true cost
#                 (straight line ≤ actual road distance — always true)
#   Consistent  : h(n) ≤ cost(n→n') + h(n')  for every successor n'
#                 (triangle inequality guarantees this for Euclidean distance)
#
# Because our heuristic is consistent, A* with a closed set is optimal.
# =============================================================================

def astar(graph: CityGraph, source: str, destination: str) -> SearchResult:
    """
    A* Search with Euclidean straight-line distance heuristic.
    Priority queue item: (f_cost, tie_breaker, g_cost, node, path)
    """
    start_time = time.perf_counter()
    nodes_explored = 0

    dest_node = graph.get_node(destination)

    # f = g + h
    h_start = heuristic(graph.get_node(source), dest_node)
    counter = 0
    frontier = [(h_start, counter, 0.0, source, [source])]
    heapq.heapify(frontier)

    # g_score: best cost found so far to reach each node
    g_score: dict[str, float] = {source: 0.0}

    while frontier:
        f, _, g, current, path = heapq.heappop(frontier)
        nodes_explored += 1

        # ── Goal Test ──
        if current == destination:
            elapsed = time.perf_counter() - start_time
            return SearchResult("A*", path, g, nodes_explored, elapsed)

        # Skip if we've already found a better path to current
        if g > g_score.get(current, float('inf')):
            continue

        # ── Expand ──
        for edge in graph.get_neighbors(current):
            neighbor = edge.node_to
            new_g    = g + edge.effective_cost

            if new_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor] = new_g
                h = heuristic(graph.get_node(neighbor), dest_node)
                new_f = new_g + h
                counter += 1
                heapq.heappush(frontier,
                               (new_f, counter, new_g, neighbor,
                                path + [neighbor]))

    elapsed = time.perf_counter() - start_time
    return SearchResult("A*", [], 0.0, nodes_explored, elapsed)


# =============================================================================
# 5. Greedy Best-First Search (GBFS)
# =============================================================================
# Strategy    : Priority queue ordered by h(n) ONLY (ignores g)
# Optimality  : NOT optimal — greedy toward goal, may miss cheaper paths
# Completeness: NOT complete (can get stuck in dead ends without visited set)
# Speed       : Often fast in practice; good for real-time applications
# Key idea    : Like A* but without the g(n) component
# =============================================================================

def greedy_bfs(graph: CityGraph, source: str, destination: str) -> SearchResult:
    """
    Greedy Best-First Search using heuristic h(n) as the priority.
    """
    start_time = time.perf_counter()
    nodes_explored = 0

    dest_node = graph.get_node(destination)
    h_start   = heuristic(graph.get_node(source), dest_node)

    counter  = 0
    frontier = [(h_start, counter, source, [source])]
    heapq.heapify(frontier)

    visited: set[str] = set()

    while frontier:
        h, _, current, path = heapq.heappop(frontier)
        nodes_explored += 1

        # ── Goal Test ──
        if current == destination:
            cost = _path_cost(graph, path)
            elapsed = time.perf_counter() - start_time
            return SearchResult("Greedy BFS", path, cost, nodes_explored, elapsed)

        if current in visited:
            continue
        visited.add(current)

        # ── Expand ──
        for edge in graph.get_neighbors(current):
            neighbor = edge.node_to
            if neighbor not in visited:
                h_n = heuristic(graph.get_node(neighbor), dest_node)
                counter += 1
                heapq.heappush(frontier,
                               (h_n, counter, neighbor, path + [neighbor]))

    elapsed = time.perf_counter() - start_time
    return SearchResult("Greedy BFS", [], 0.0, nodes_explored, elapsed)


# =============================================================================
# Helper — Compute actual path cost
# =============================================================================

def _path_cost(graph: CityGraph, path: list[str]) -> float:
    """Sum effective_cost along a path list."""
    total = 0.0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        for edge in graph.edges[a]:
            if edge.node_to == b:
                total += edge.effective_cost
                break
    return round(total, 2)


# =============================================================================
# Run ALL algorithms and return list of SearchResult
# =============================================================================

def run_all(graph: CityGraph, source: str, destination: str) -> list[SearchResult]:
    """Convenience: run every algorithm and return results list."""
    algorithms = [bfs, dfs, ucs, astar, greedy_bfs]
    results = []
    for algo in algorithms:
        result = algo(graph, source, destination)
        results.append(result)
    return results
