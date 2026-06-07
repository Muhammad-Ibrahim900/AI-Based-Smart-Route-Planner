# =============================================================================
# graph.py — Graph Representation for Smart Route Planner
# =============================================================================
# Represents the city map as a weighted, undirected graph.
# Nodes = locations (e.g. Islamabad sectors)
# Edges = roads with distance (cost) and optional traffic weight
# =============================================================================

class Node:
    """
    Represents a location (city sector/landmark) on the map.
    Each node has:
      - name       : unique string identifier (e.g. "F-6")
      - x, y       : 2D coordinates used for heuristic + visual drawing
    """
    def __init__(self, name: str, x: float, y: float):
        self.name = name
        self.x = x          # pixel / logical x-coordinate
        self.y = y          # pixel / logical y-coordinate

    def __repr__(self):
        return f"Node({self.name})"


class Edge:
    """
    Represents a road between two nodes.
    Attributes:
      - node_from  : source node name
      - node_to    : destination node name
      - distance   : base road length / cost
      - traffic    : traffic multiplier (1.0 = free flow, >1 = congestion)
                     effective_cost = distance * traffic
      - blocked    : if True, this road is closed (bonus feature)
    """
    def __init__(self, node_from: str, node_to: str,
                 distance: float, traffic: float = 1.0, blocked: bool = False):
        self.node_from = node_from
        self.node_to   = node_to
        self.distance  = distance
        self.traffic   = traffic
        self.blocked   = blocked

    @property
    def effective_cost(self) -> float:
        """Cost after applying traffic weight. Blocked roads return infinity."""
        if self.blocked:
            return float('inf')
        return round(self.distance * self.traffic, 2)

    def __repr__(self):
        return (f"Edge({self.node_from} -> {self.node_to} | "
                f"dist={self.distance} | traffic={self.traffic} | "
                f"cost={self.effective_cost} | blocked={self.blocked})")


class CityGraph:
    """
    The main graph class using an adjacency list representation.

    Internally stores:
      - self.nodes : dict[name -> Node]
      - self.edges : dict[name -> list[Edge]]   (adjacency list)

    The graph is UNDIRECTED: adding an edge A->B also adds B->A.
    """

    def __init__(self):
        self.nodes: dict[str, Node]       = {}
        self.edges: dict[str, list[Edge]] = {}

    # ------------------------------------------------------------------
    # Graph construction helpers
    # ------------------------------------------------------------------

    def add_node(self, name: str, x: float, y: float) -> None:
        """Add a location node to the map."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists.")
        self.nodes[name]  = Node(name, x, y)
        self.edges[name]  = []

    def add_edge(self, from_name: str, to_name: str,
                 distance: float, traffic: float = 1.0) -> None:
        """
        Add a bidirectional road between two existing nodes.
        distance : base road length (km)
        traffic  : multiplier (1.0 = no congestion)
        """
        self._check_node(from_name)
        self._check_node(to_name)
        # Forward direction
        self.edges[from_name].append(Edge(from_name, to_name, distance, traffic))
        # Reverse direction (undirected graph)
        self.edges[to_name].append(Edge(to_name, from_name, distance, traffic))

    # ------------------------------------------------------------------
    # Bonus: Dynamic features
    # ------------------------------------------------------------------

    def set_traffic(self, from_name: str, to_name: str, traffic: float) -> None:
        """Update traffic multiplier on a road in both directions."""
        self._update_edge_attr(from_name, to_name, 'traffic', traffic)
        self._update_edge_attr(to_name, from_name, 'traffic', traffic)

    def block_road(self, from_name: str, to_name: str, blocked: bool = True) -> None:
        """Block or unblock a road in both directions."""
        self._update_edge_attr(from_name, to_name, 'blocked', blocked)
        self._update_edge_attr(to_name, from_name, 'blocked', blocked)

    def _update_edge_attr(self, from_name: str, to_name: str,
                          attr: str, value) -> None:
        for edge in self.edges.get(from_name, []):
            if edge.node_to == to_name:
                setattr(edge, attr, value)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_neighbors(self, name: str) -> list[Edge]:
        """Return all non-blocked edges from a given node."""
        return [e for e in self.edges.get(name, []) if not e.blocked]

    def get_node(self, name: str) -> Node:
        self._check_node(name)
        return self.nodes[name]

    def node_names(self) -> list[str]:
        return sorted(self.nodes.keys())

    def _check_node(self, name: str) -> None:
        if name not in self.nodes:
            raise ValueError(f"Node '{name}' not found in graph.")

    # ------------------------------------------------------------------
    # Pretty print
    # ------------------------------------------------------------------

    def display(self) -> None:
        print("\n" + "="*60)
        print("  CITY MAP — ADJACENCY LIST")
        print("="*60)
        for node_name in self.node_names():
            neighbors = self.edges[node_name]
            n_str = ", ".join(
                f"{e.node_to}(cost={e.effective_cost})" for e in neighbors
            )
            print(f"  {node_name:12s} -> {n_str if n_str else 'No connections'}")
        print("="*60 + "\n")


# =============================================================================
# build_islamabad_map()
# Creates a hardcoded map of Islamabad sectors (10–15 nodes).
# Coordinates are logical (canvas pixel positions for Tkinter drawing).
# =============================================================================

def build_islamabad_map() -> CityGraph:
    """
    Returns a CityGraph representing key Islamabad sectors and landmarks.

    Node layout (approximate canvas positions, 800x600 canvas):
    ┌─────────────────────────────────────────────────────────────────┐
    │  F-6  ── F-7  ── F-8  ── F-10                                  │
    │   |       |       |        |                                    │
    │  G-6  ── G-7  ── G-8  ── G-10 ── G-11                         │
    │   |               |                |                            │
    │  H-8 ── Blue Area  Blue Area      I-8                          │
    │                   |                                             │
    │              Centaurus                                          │
    └─────────────────────────────────────────────────────────────────┘

    Distances are in km (approximate real values).
    Traffic weights can be updated dynamically.
    """

    g = CityGraph()

    # ── Nodes (name, canvas_x, canvas_y) ─────────────────────────────
    g.add_node("F-6",       120, 100)
    g.add_node("F-7",       250, 100)
    g.add_node("F-8",       380, 100)
    g.add_node("F-10",      510, 100)
    g.add_node("G-6",       120, 230)
    g.add_node("G-7",       250, 230)
    g.add_node("G-8",       380, 230)
    g.add_node("G-10",      510, 230)
    g.add_node("G-11",      640, 230)
    g.add_node("H-8",       160, 360)
    g.add_node("Blue Area", 380, 360)
    g.add_node("Centaurus", 310, 460)
    g.add_node("I-8",       640, 360)
    g.add_node("Shakar Parian", 200, 490)
    g.add_node("Rawal Lake", 560, 460)

    # ── Edges (from, to, distance_km, traffic_multiplier) ────────────
    # Row 1: F-sector connections
    g.add_edge("F-6",  "F-7",       2.5,  1.2)   # moderate traffic
    g.add_edge("F-7",  "F-8",       2.0,  1.0)
    g.add_edge("F-8",  "F-10",      3.5,  1.0)

    # Column: F-sector to G-sector
    g.add_edge("F-6",  "G-6",       3.0,  1.0)
    g.add_edge("F-7",  "G-7",       3.0,  1.5)   # heavy traffic
    g.add_edge("F-8",  "G-8",       3.0,  1.0)
    g.add_edge("F-10", "G-10",      3.0,  1.0)

    # Row 2: G-sector connections
    g.add_edge("G-6",  "G-7",       2.5,  1.0)
    g.add_edge("G-7",  "G-8",       2.0,  1.3)
    g.add_edge("G-8",  "G-10",      3.5,  1.0)
    g.add_edge("G-10", "G-11",      2.0,  1.0)

    # Column: G-sector to H/I-sector
    g.add_edge("G-6",  "H-8",       4.0,  1.0)
    g.add_edge("G-8",  "Blue Area", 2.5,  1.4)   # congested area
    g.add_edge("G-11", "I-8",       2.5,  1.0)

    # Row 3: Lower connections
    g.add_edge("H-8",       "Blue Area",    3.0,  1.0)
    g.add_edge("H-8",       "Shakar Parian",2.5,  1.0)
    g.add_edge("Blue Area", "Centaurus",    1.5,  1.8)  # very busy
    g.add_edge("Blue Area", "Rawal Lake",   4.0,  1.0)
    g.add_edge("Centaurus", "Shakar Parian",2.0,  1.0)
    g.add_edge("I-8",       "Rawal Lake",   3.0,  1.0)
    g.add_edge("Rawal Lake","G-11",         2.5,  1.0)

    return g
