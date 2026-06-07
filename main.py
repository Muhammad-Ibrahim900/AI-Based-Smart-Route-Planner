# =============================================================================
# main.py — Entry Point for AI Smart Route Planner
# =============================================================================
# Run modes:
#   python main.py          → launches Tkinter GUI (default)
#   python main.py --console → interactive console interface
# =============================================================================

import sys
import os

from graph import build_islamabad_map
from algorithms import bfs, dfs, ucs, astar, greedy_bfs, run_all
from utils import (print_comparison, print_path_detail,
                   validate_nodes)


# =============================================================================
# Console-Based Interactive Interface
# =============================================================================

def run_console():
    """
    A clean, interactive command-line interface.
    Works on any platform without needing a display.
    """
    graph = build_islamabad_map()

    _banner()
    graph.display()

    while True:
        print("\n" + "─"*55)
        print("  MAIN MENU")
        print("─"*55)
        print("  [1] Find Route (single algorithm)")
        print("  [2] Compare ALL Algorithms")
        print("  [3] Simulate Traffic (randomize weights)")
        print("  [4] Block / Unblock a Road")
        print("  [5] Display Map (adjacency list)")
        print("  [6] Show Node List")
        print("  [0] Exit")
        print("─"*55)

        choice = input("  Enter choice: ").strip()

        if choice == "0":
            print("\n  Goodbye! 👋\n")
            break

        elif choice == "1":
            _menu_single(graph)

        elif choice == "2":
            _menu_compare_all(graph)

        elif choice == "3":
            _menu_traffic(graph)

        elif choice == "4":
            _menu_block(graph)

        elif choice == "5":
            graph.display()

        elif choice == "6":
            _show_nodes(graph)

        else:
            print("  ✗ Invalid choice. Please try again.")


def _banner():
    print("""
╔══════════════════════════════════════════════════════╗
║      AI-Based Smart Route Planner                   ║
║      Using Classical Search Algorithms              ║
║                                                      ║
║      Map: Islamabad City Sectors                    ║
║      Algorithms: BFS | DFS | UCS | A* | Greedy     ║
╚══════════════════════════════════════════════════════╝
""")


def _show_nodes(graph):
    print("\n  Available Locations:")
    print("  " + "─"*40)
    for i, name in enumerate(graph.node_names(), 1):
        print(f"  {i:2d}. {name}")
    print()


def _get_src_dst(graph) -> tuple[str, str] | None:
    """Prompt for source and destination, validate, return or None."""
    _show_nodes(graph)
    src = input("  Enter SOURCE location: ").strip()
    dst = input("  Enter DESTINATION location: ").strip()
    valid, err = validate_nodes(graph, src, dst)
    if not valid:
        print(f"\n  ✗ Error: {err}")
        return None
    return src, dst


def _menu_single(graph):
    print("\n  ── Single Algorithm ──")
    print("  Algorithms: BFS | DFS | UCS | A* | Greedy BFS")
    algo_name = input("  Choose algorithm: ").strip().upper()

    algo_map = {
        "BFS":        bfs,
        "DFS":        dfs,
        "UCS":        ucs,
        "A*":         astar,
        "A":          astar,   # shortcut
        "GREEDY BFS": greedy_bfs,
        "GREEDY":     greedy_bfs,
    }
    algo_fn = algo_map.get(algo_name)
    if algo_fn is None:
        print(f"  ✗ Unknown algorithm '{algo_name}'.")
        return

    nodes = _get_src_dst(graph)
    if nodes is None:
        return
    src, dst = nodes

    print(f"\n  Running {algo_name} from '{src}' to '{dst}'…")
    result = algo_fn(graph, src, dst)
    print(result.summary())
    print_path_detail(graph, result)


def _menu_compare_all(graph):
    print("\n  ── Compare All Algorithms ──")
    nodes = _get_src_dst(graph)
    if nodes is None:
        return
    src, dst = nodes

    print(f"\n  Running all algorithms from '{src}' to '{dst}'…\n")
    results = run_all(graph, src, dst)

    for r in results:
        print(r.summary())

    print_comparison(results)

    # Detailed breakdown of A* (optimal)
    astar_result = next((r for r in results if r.algorithm == "A*"), None)
    if astar_result:
        print_path_detail(graph, astar_result)


def _menu_traffic(graph):
    import random
    print("\n  ── Traffic Simulation ──")
    print("  Randomising traffic multipliers on all roads…")
    for node_edges in graph.edges.values():
        for edge in node_edges:
            edge.traffic = round(random.uniform(1.0, 2.5), 2)
    print("  ✓ Traffic updated! Run a search to see new costs.")
    graph.display()


def _menu_block(graph):
    print("\n  ── Block / Unblock Road ──")
    _show_nodes(graph)
    a = input("  Enter first node: ").strip()
    b = input("  Enter second node: ").strip()

    # Check edge exists
    found = False
    for edge in graph.edges.get(a, []):
        if edge.node_to == b:
            found = True
            new_state = not edge.blocked
            graph.block_road(a, b, new_state)
            state_str = "BLOCKED 🚧" if new_state else "UNBLOCKED ✓"
            print(f"\n  Road {a} ↔ {b} is now {state_str}")
            break
    if not found:
        print(f"  ✗ No direct road between '{a}' and '{b}'.")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    args = sys.argv[1:]

    if "--console" in args:
        run_console()
    else:
        # Try to launch GUI; fall back to console if no display
        try:
            import tkinter as tk
            # Quick test: will raise if no display available
            test = tk.Tk()
            test.destroy()
            from ui import launch_gui
            launch_gui()
        except Exception as e:
            print(f"  [GUI unavailable: {e}]")
            print("  Falling back to console mode…\n")
            run_console()


if __name__ == "__main__":
    main()
