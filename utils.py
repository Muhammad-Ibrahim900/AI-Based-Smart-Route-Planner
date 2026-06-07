# =============================================================================
# utils.py — Utility Functions for Smart Route Planner
# =============================================================================
# Contains:
#   heuristic()         — Euclidean straight-line distance for A*
#   reconstruct_path()  — (unused here; path tracked inline in algorithms)
#   print_comparison()  — Comparison table for all algorithm results
#   print_path_detail() — Verbose step-by-step path breakdown
# =============================================================================

import math
from graph import Node


# =============================================================================
# HEURISTIC FUNCTION  (used by A* and Greedy BFS)
# =============================================================================
# We use the EUCLIDEAN STRAIGHT-LINE DISTANCE between two nodes' coordinates.
#
# Formula:  h(n) = sqrt( (x_n - x_goal)² + (y_n - y_goal)² )
#
# WHY THIS WORKS:
#   The canvas coordinates are set proportionally so that 1 unit ≈ 1 km.
#   (In build_islamabad_map we spaced nodes ~130 px apart for ~2-3 km gaps,
#    and we apply a scaling factor of 0.02 to convert px → km.)
#
# ADMISSIBILITY:
#   A heuristic h(n) is admissible if:  h(n) ≤ h*(n)  for all n
#   where h*(n) is the TRUE cost from n to the goal.
#
#   Proof: The straight-line distance between any two points is ALWAYS less
#   than or equal to the actual road distance (you can't drive a shorter
#   path than a straight line). Therefore h(n) ≤ h*(n). ✓
#
# CONSISTENCY (Monotonicity):
#   A heuristic is consistent if for every node n and successor n':
#       h(n) ≤ cost(n → n') + h(n')
#
#   Proof: This is guaranteed by the TRIANGLE INEQUALITY of Euclidean space.
#   dist(n, goal) ≤ dist(n, n') + dist(n', goal)  ← triangle inequality
#   Because cost(n→n') ≥ dist(n,n') (road is never shorter than straight line),
#   consistency follows. ✓
#
# CONSEQUENCE:
#   Because our heuristic is both admissible AND consistent, A* with a
#   closed set (visited nodes not re-expanded) is GUARANTEED to find the
#   optimal (minimum cost) path.
# =============================================================================

SCALE = 0.02  # pixels → km conversion factor (tune to match your map scale)

def heuristic(node: Node, goal: Node) -> float:
    """
    Euclidean straight-line distance heuristic.
    Returns an estimated cost (km) from `node` to `goal`.

    Admissible  : True  (never overestimates)
    Consistent  : True  (triangle inequality holds)
    """
    dx = node.x - goal.x
    dy = node.y - goal.y
    return round(math.sqrt(dx * dx + dy * dy) * SCALE, 4)


# =============================================================================
# Path reconstruction (helper if parent-dict style is used)
# =============================================================================

def reconstruct_path(came_from: dict[str, str | None], source: str,
                     destination: str) -> list[str]:
    """
    Reconstruct path from a came_from dict (parent map).
    Used when algorithms store {node: parent} instead of full path lists.
    Returns the path as a list from source to destination.
    """
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    path.reverse()
    # Validate: path must start at source
    if path and path[0] == source:
        return path
    return []    # No valid path


# =============================================================================
# Comparison Table Printer
# =============================================================================

def print_comparison(results: list) -> None:
    """
    Print a formatted comparison table of all algorithm results.

    Example output:
    ┌──────────────┬────────────┬────────────────┬─────────────┐
    │ Algorithm    │ Path Cost  │ Nodes Explored │ Time (ms)   │
    ├──────────────┼────────────┼────────────────┼─────────────┤
    │ BFS          │  14.30 km  │      6         │  0.041 ms   │
    │ DFS          │  22.10 km  │      9         │  0.019 ms   │
    │ UCS          │  12.50 km  │      8         │  0.055 ms   │
    │ A*           │  12.50 km  │      5         │  0.038 ms   │
    │ Greedy BFS   │  13.80 km  │      4         │  0.022 ms   │
    └──────────────┴────────────┴────────────────┴─────────────┘
    """
    # Column widths
    w1, w2, w3, w4 = 16, 12, 16, 14

    top    = f"┌{'─'*w1}┬{'─'*w2}┬{'─'*w3}┬{'─'*w4}┐"
    header = (f"│ {'Algorithm':<{w1-2}} │ {'Path Cost':^{w2-2}} │"
              f" {'Nodes Explored':^{w3-2}} │ {'Time (ms)':^{w4-2}} │")
    sep    = f"├{'─'*w1}┼{'─'*w2}┼{'─'*w3}┼{'─'*w4}┤"
    bottom = f"└{'─'*w1}┴{'─'*w2}┴{'─'*w3}┴{'─'*w4}┘"

    print("\n" + "="*65)
    print("  ALGORITHM COMPARISON TABLE")
    print("="*65)
    print(top)
    print(header)
    print(sep)

    for r in results:
        if r.found():
            cost_str = f"{r.total_cost:.2f} km"
            time_str = f"{r.time_taken * 1000:.4f} ms"
        else:
            cost_str = "No path"
            time_str = f"{r.time_taken * 1000:.4f} ms"

        row = (f"│ {r.algorithm:<{w1-2}} │ {cost_str:^{w2-2}} │"
               f" {r.nodes_explored:^{w3-2}} │ {time_str:^{w4-2}} │")
        print(row)

    print(bottom)
    print()

    # ── Highlight winner ──
    found = [r for r in results if r.found()]
    if found:
        optimal = min(found, key=lambda r: r.total_cost)
        fastest = min(found, key=lambda r: r.nodes_explored)
        print(f"  🏆 Optimal Path   : {optimal.algorithm}"
              f" (cost = {optimal.total_cost:.2f} km)")
        print(f"  ⚡ Fewest Explored: {fastest.algorithm}"
              f" ({fastest.nodes_explored} nodes)\n")


# =============================================================================
# Detailed Path Breakdown
# =============================================================================

def print_path_detail(graph, result) -> None:
    """Print step-by-step breakdown of a path with individual edge costs."""
    if not result.found():
        print(f"\n[{result.algorithm}] No path found.\n")
        return

    print(f"\n{'='*55}")
    print(f"  {result.algorithm} — Path Detail")
    print(f"{'='*55}")

    path = result.path
    running_cost = 0.0

    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        # Find edge cost
        edge_cost = 0.0
        for edge in graph.edges[a]:
            if edge.node_to == b:
                edge_cost = edge.effective_cost
                break
        running_cost += edge_cost
        print(f"  {a:15s} → {b:15s}  | segment: {edge_cost:5.2f} km"
              f"  | cumulative: {running_cost:5.2f} km")

    print(f"{'─'*55}")
    print(f"  TOTAL COST: {result.total_cost:.2f} km")
    print(f"  Nodes Explored: {result.nodes_explored}")
    print(f"  Time Taken: {result.time_taken*1000:.4f} ms")
    print(f"{'='*55}\n")


# =============================================================================
# Input Validation Helper
# =============================================================================

def validate_nodes(graph, source: str, destination: str) -> tuple[bool, str]:
    """
    Validate that source and destination exist in the graph and are different.
    Returns (is_valid: bool, error_message: str)
    """
    if source not in graph.nodes:
        return False, f"Source '{source}' not found in the map."
    if destination not in graph.nodes:
        return False, f"Destination '{destination}' not found in the map."
    if source == destination:
        return False, "Source and destination must be different locations."
    return True, ""
