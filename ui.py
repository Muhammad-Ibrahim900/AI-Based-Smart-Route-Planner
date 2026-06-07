# =============================================================================
# ui.py — Tkinter GUI for Smart Route Planner
# =============================================================================
# Features:
#   • Draws all nodes and edges on a canvas
#   • User selects source & destination from dropdowns
#   • Runs selected algorithm (or ALL at once)
#   • Highlights the found path in red/orange
#   • Shows comparison table in a side panel
#   • Traffic simulation: randomize traffic weights
#   • Block road: click two nodes to block/unblock an edge
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading

from graph import CityGraph, build_islamabad_map
from algorithms import bfs, dfs, ucs, astar, greedy_bfs, run_all, SearchResult
from utils import print_comparison, print_path_detail, validate_nodes


# ── Color palette ──────────────────────────────────────────────────────────
CLR_BG         = "#1e1e2e"   # dark canvas background
CLR_EDGE       = "#555577"   # normal edge colour
CLR_EDGE_BLOCK = "#ff4444"   # blocked edge
CLR_EDGE_HIGH  = "#f0a500"   # highlighted path edge
CLR_NODE       = "#7c3aed"   # normal node fill (purple)
CLR_NODE_SRC   = "#22c55e"   # source node (green)
CLR_NODE_DST   = "#ef4444"   # destination node (red)
CLR_NODE_PATH  = "#f97316"   # path node (orange)
CLR_NODE_TEXT  = "#ffffff"   # node label text
CLR_SIDEBAR    = "#12122a"   # sidebar background
CLR_TEXT       = "#e2e8f0"   # general text
CLR_ACCENT     = "#7c3aed"   # accent / button colour
CLR_BTN        = "#4c1d95"
CLR_BTN_HOVER  = "#6d28d9"

NODE_R         = 22          # node circle radius (pixels)
FONT_NODE      = ("Consolas", 8, "bold")
FONT_LABEL     = ("Segoe UI", 9)
FONT_HEADER    = ("Segoe UI", 11, "bold")
FONT_MONO      = ("Consolas", 9)


# =============================================================================
class RoutePlannerApp:
    """Main Tkinter application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI Smart Route Planner — Islamabad")
        self.root.configure(bg=CLR_BG)
        self.root.resizable(True, True)

        # ── Graph ──
        self.graph: CityGraph = build_islamabad_map()

        # ── State ──
        self.current_results: list[SearchResult] = []
        self.highlighted_path: list[str]         = []
        self.block_mode: bool                    = False
        self.block_selection: list[str]          = []

        self._build_ui()
        self._draw_graph()

    # ==========================================================================
    # UI Layout
    # ==========================================================================

    def _build_ui(self):
        """Construct all widgets."""
        # ── Top bar ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg="#0f0f1f", pady=6)
        topbar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(topbar, text="🗺  AI Smart Route Planner",
                 font=("Segoe UI", 15, "bold"),
                 fg="#a78bfa", bg="#0f0f1f").pack(side=tk.LEFT, padx=16)

        tk.Label(topbar, text="Islamabad City Map  |  AI Search Algorithms",
                 font=("Segoe UI", 9), fg="#94a3b8",
                 bg="#0f0f1f").pack(side=tk.LEFT, padx=4)

        # ── Main area: canvas + sidebar ──────────────────────────────────────
        main_frame = tk.Frame(self.root, bg=CLR_BG)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas (left)
        self.canvas = tk.Canvas(main_frame, width=780, height=580,
                                bg=CLR_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Sidebar (right)
        sidebar = tk.Frame(main_frame, bg=CLR_SIDEBAR, width=300)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready. Select source and destination.")
        statusbar = tk.Label(self.root, textvariable=self.status_var,
                             font=("Segoe UI", 9), fg="#94a3b8",
                             bg="#0f0f1f", anchor="w", padx=10, pady=4)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_sidebar(self, parent):
        pad = dict(padx=12, pady=4)

        # Title
        tk.Label(parent, text="Route Controls",
                 font=FONT_HEADER, fg="#a78bfa",
                 bg=CLR_SIDEBAR).pack(pady=(14, 4))
        tk.Frame(parent, bg="#4c1d95", height=2).pack(fill=tk.X, padx=12, pady=2)

        # ── Source ──
        tk.Label(parent, text="Source:", font=FONT_LABEL,
                 fg=CLR_TEXT, bg=CLR_SIDEBAR).pack(anchor="w", **pad)
        self.src_var = tk.StringVar(value="F-6")
        self.src_combo = ttk.Combobox(parent, textvariable=self.src_var,
                                      values=self.graph.node_names(),
                                      state="readonly", width=24)
        self.src_combo.pack(**pad)
        self.src_combo.bind("<<ComboboxSelected>>", lambda e: self._draw_graph())

        # ── Destination ──
        tk.Label(parent, text="Destination:", font=FONT_LABEL,
                 fg=CLR_TEXT, bg=CLR_SIDEBAR).pack(anchor="w", **pad)
        self.dst_var = tk.StringVar(value="Rawal Lake")
        self.dst_combo = ttk.Combobox(parent, textvariable=self.dst_var,
                                      values=self.graph.node_names(),
                                      state="readonly", width=24)
        self.dst_combo.pack(**pad)
        self.dst_combo.bind("<<ComboboxSelected>>", lambda e: self._draw_graph())

        # ── Algorithm selector ──
        tk.Label(parent, text="Algorithm:", font=FONT_LABEL,
                 fg=CLR_TEXT, bg=CLR_SIDEBAR).pack(anchor="w", **pad)
        self.algo_var = tk.StringVar(value="A*")
        algo_combo = ttk.Combobox(
            parent, textvariable=self.algo_var,
            values=["BFS", "DFS", "UCS", "A*", "Greedy BFS", "Run ALL"],
            state="readonly", width=24)
        algo_combo.pack(**pad)

        # ── Buttons ──
        btn_cfg = dict(font=("Segoe UI", 10, "bold"),
                       fg="white", relief="flat",
                       activeforeground="white", cursor="hand2",
                       pady=7, padx=8, bd=0)

        tk.Button(parent, text="▶  Find Route",
                  bg="#4c1d95", activebackground="#6d28d9",
                  command=self._run_algorithm,
                  **btn_cfg).pack(fill=tk.X, padx=12, pady=(10, 4))

        tk.Button(parent, text="🔄  Simulate Traffic",
                  bg="#0f4c75", activebackground="#1a6fa3",
                  command=self._simulate_traffic,
                  **btn_cfg).pack(fill=tk.X, padx=12, pady=4)

        tk.Button(parent, text="🚧  Block Road Mode",
                  bg="#7f1d1d", activebackground="#991b1b",
                  command=self._toggle_block_mode,
                  **btn_cfg).pack(fill=tk.X, padx=12, pady=4)

        tk.Button(parent, text="↺  Reset Map",
                  bg="#374151", activebackground="#4b5563",
                  command=self._reset_map,
                  **btn_cfg).pack(fill=tk.X, padx=12, pady=4)

        tk.Frame(parent, bg="#4c1d95", height=2).pack(fill=tk.X, padx=12, pady=8)

        # ── Results area ──
        tk.Label(parent, text="Results", font=FONT_HEADER,
                 fg="#a78bfa", bg=CLR_SIDEBAR).pack(anchor="w", padx=12)

        results_frame = tk.Frame(parent, bg=CLR_SIDEBAR)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.results_text = tk.Text(
            results_frame, wrap=tk.WORD,
            bg="#0a0a1a", fg=CLR_TEXT,
            font=FONT_MONO, relief="flat",
            state=tk.DISABLED, padx=6, pady=6)
        scrollbar = tk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.pack(fill=tk.BOTH, expand=True)

    # ==========================================================================
    # Drawing
    # ==========================================================================

    def _draw_graph(self, highlight: list[str] | None = None):
        """Redraw the entire canvas."""
        self.canvas.delete("all")
        highlight = highlight or self.highlighted_path
        path_edges = set()

        # Build set of path edges for fast lookup
        if highlight and len(highlight) > 1:
            for i in range(len(highlight) - 1):
                path_edges.add((highlight[i], highlight[i+1]))
                path_edges.add((highlight[i+1], highlight[i]))

        # ── Draw edges ──
        drawn_edges = set()
        for node_name, edges in self.graph.edges.items():
            for edge in edges:
                key = tuple(sorted([edge.node_from, edge.node_to]))
                if key in drawn_edges:
                    continue
                drawn_edges.add(key)

                n1 = self.graph.nodes[edge.node_from]
                n2 = self.graph.nodes[edge.node_to]

                is_path  = (edge.node_from, edge.node_to) in path_edges
                is_block = edge.blocked

                clr   = (CLR_EDGE_BLOCK if is_block
                         else CLR_EDGE_HIGH if is_path else CLR_EDGE)
                width = 4 if is_path else 2

                self.canvas.create_line(
                    n1.x, n1.y, n2.x, n2.y,
                    fill=clr, width=width,
                    tags=("edge", f"edge_{key[0]}_{key[1]}")
                )
                # Edge cost label
                mid_x = (n1.x + n2.x) / 2
                mid_y = (n1.y + n2.y) / 2
                if not is_block:
                    effective = round(edge.distance * edge.traffic, 1)
                    lbl_clr = "#f0a500" if is_path else "#667"
                    self.canvas.create_text(
                        mid_x + 6, mid_y - 6,
                        text=f"{effective}km",
                        fill=lbl_clr,
                        font=("Consolas", 7))

        # ── Draw nodes ──
        src = self.src_var.get()
        dst = self.dst_var.get()

        for name, node in self.graph.nodes.items():
            # Determine colour
            if name == src:
                fill = CLR_NODE_SRC
            elif name == dst:
                fill = CLR_NODE_DST
            elif highlight and name in highlight and name not in (src, dst):
                fill = CLR_NODE_PATH
            else:
                fill = CLR_NODE

            outline_w = 3 if name in (src, dst) else 1
            outline_c = "#fff" if name in (src, dst) else "#aaa"

            self.canvas.create_oval(
                node.x - NODE_R, node.y - NODE_R,
                node.x + NODE_R, node.y + NODE_R,
                fill=fill, outline=outline_c,
                width=outline_w,
                tags=("node", f"node_{name}")
            )
            self.canvas.create_text(
                node.x, node.y,
                text=name, fill=CLR_NODE_TEXT,
                font=FONT_NODE, tags=f"node_lbl_{name}")

        # ── Legend ──
        self._draw_legend()

    def _draw_legend(self):
        lx, ly = 20, 520
        items = [
            (CLR_NODE_SRC,  "Source"),
            (CLR_NODE_DST,  "Destination"),
            (CLR_NODE_PATH, "Path"),
            (CLR_NODE,      "Location"),
        ]
        for i, (clr, label) in enumerate(items):
            ox = lx + i * 115
            self.canvas.create_oval(ox, ly, ox+14, ly+14,
                                    fill=clr, outline="#fff")
            self.canvas.create_text(ox + 22, ly + 7,
                                    text=label, fill=CLR_TEXT,
                                    font=("Segoe UI", 8), anchor="w")

    # ==========================================================================
    # Algorithm runner
    # ==========================================================================

    def _run_algorithm(self):
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()

        valid, err = validate_nodes(self.graph, src, dst)
        if not valid:
            messagebox.showerror("Input Error", err)
            return

        algo = self.algo_var.get()
        self._set_status(f"Running {algo}…")

        def _execute():
            algo_map = {
                "BFS":       bfs,
                "DFS":       dfs,
                "UCS":       ucs,
                "A*":        astar,
                "Greedy BFS": greedy_bfs,
            }
            if algo == "Run ALL":
                results = run_all(self.graph, src, dst)
            else:
                results = [algo_map[algo](self.graph, src, dst)]

            self.current_results = results
            # Highlight path of best result (by cost)
            found = [r for r in results if r.found()]
            if found:
                best = min(found, key=lambda r: r.total_cost)
                self.highlighted_path = best.path
            else:
                self.highlighted_path = []

            self.root.after(0, self._on_results_ready, results)

        threading.Thread(target=_execute, daemon=True).start()

    def _on_results_ready(self, results: list[SearchResult]):
        self._draw_graph(self.highlighted_path)
        self._display_results(results)
        found = [r for r in results if r.found()]
        if found:
            best = min(found, key=lambda r: r.total_cost)
            self._set_status(
                f"✔ Best: {best.algorithm}  |  "
                f"Path: {' → '.join(best.path)}  |  "
                f"Cost: {best.total_cost:.2f} km")
        else:
            self._set_status("✘ No path found between selected nodes.")

    def _display_results(self, results: list[SearchResult]):
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)

        for r in results:
            if r.found():
                self.results_text.insert(tk.END,
                    f"{'─'*30}\n"
                    f"[{r.algorithm}]\n"
                    f"Path   : {' → '.join(r.path)}\n"
                    f"Cost   : {r.total_cost:.2f} km\n"
                    f"Nodes  : {r.nodes_explored}\n"
                    f"Time   : {r.time_taken*1000:.4f} ms\n"
                )
            else:
                self.results_text.insert(tk.END,
                    f"{'─'*30}\n"
                    f"[{r.algorithm}] No path found.\n")

        if len(results) > 1:
            found = [r for r in results if r.found()]
            if found:
                opt = min(found, key=lambda r: r.total_cost)
                fst = min(found, key=lambda r: r.nodes_explored)
                self.results_text.insert(tk.END,
                    f"\n{'='*30}\n"
                    f"🏆 Optimal : {opt.algorithm} ({opt.total_cost:.2f} km)\n"
                    f"⚡ Fastest  : {fst.algorithm} ({fst.nodes_explored} nodes)\n")

        self.results_text.configure(state=tk.DISABLED)

    # ==========================================================================
    # Bonus Features
    # ==========================================================================

    def _simulate_traffic(self):
        """Randomly assign new traffic weights to all edges."""
        for node_edges in self.graph.edges.values():
            for edge in node_edges:
                edge.traffic = round(random.uniform(1.0, 2.5), 2)
        self.highlighted_path = []
        self._draw_graph()
        self._set_status("Traffic simulated! Edge weights updated randomly.")

    def _toggle_block_mode(self):
        self.block_mode = not self.block_mode
        self.block_selection = []
        if self.block_mode:
            self._set_status("Block mode ON — click two nodes to block/unblock a road.")
        else:
            self._set_status("Block mode OFF.")

    def _on_canvas_click(self, event):
        """Handle canvas clicks for block-road feature."""
        if not self.block_mode:
            return
        # Find nearest node to click
        clicked = self._nearest_node(event.x, event.y)
        if clicked is None:
            return
        if clicked not in self.block_selection:
            self.block_selection.append(clicked)
            self._set_status(
                f"Block mode: selected '{clicked}' "
                f"({len(self.block_selection)}/2 nodes)")

        if len(self.block_selection) == 2:
            a, b = self.block_selection
            # Find and toggle edge
            toggled = False
            for edge in self.graph.edges.get(a, []):
                if edge.node_to == b:
                    new_state = not edge.blocked
                    self.graph.block_road(a, b, new_state)
                    action = "blocked" if new_state else "unblocked"
                    self._set_status(f"Road {a} ↔ {b} has been {action}.")
                    toggled = True
                    break
            if not toggled:
                self._set_status(f"No direct road between '{a}' and '{b}'.")
            self.block_selection = []
            self._draw_graph()

    def _nearest_node(self, cx: int, cy: int, threshold: int = 30) -> str | None:
        """Return the name of the node nearest to canvas click, or None."""
        best_name = None
        best_dist = float('inf')
        for name, node in self.graph.nodes.items():
            dist = ((node.x - cx)**2 + (node.y - cy)**2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_name = name
        return best_name if best_dist <= threshold else None

    def _reset_map(self):
        """Reload a fresh graph and clear state."""
        self.graph            = build_islamabad_map()
        self.highlighted_path = []
        self.block_mode       = False
        self.block_selection  = []
        self.current_results  = []
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.configure(state=tk.DISABLED)
        self._draw_graph()
        self._set_status("Map reset to defaults.")

    # ==========================================================================
    # Helpers
    # ==========================================================================

    def _set_status(self, msg: str):
        self.status_var.set(msg)


# =============================================================================
# Launch
# =============================================================================

def launch_gui():
    root = tk.Tk()
    # Apply ttk styling
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground="#1e1e3e",
                    background="#1e1e3e",
                    foreground="#e2e8f0",
                    selectbackground="#4c1d95")

    app = RoutePlannerApp(root)
    root.minsize(1100, 640)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
