# AI-Based Smart Route Planner Using Search Algorithms

**Course**: Artificial Intelligence  
**Language**: Python 3.10+  
**Map**: Islamabad City Sectors (15 nodes)  
**Algorithms**: BFS · DFS · UCS · A* · Greedy Best-First Search

---

## 📁 Project Structure

```
smart_route_planner/
├── graph.py        # CityGraph, Node, Edge classes + Islamabad map data
├── algorithms.py   # BFS, DFS, UCS, A*, Greedy BFS implementations
├── utils.py        # Heuristic, comparison table, path detail printer
├── ui.py           # Tkinter GUI with map visualization
├── main.py         # Entry point (GUI or console mode)
└── README.md       # This file
```

---

## ▶ How to Run

### Requirements
- Python 3.10 or newer  
- `tkinter` (bundled with Python on Windows/Mac; on Ubuntu: `sudo apt install python3-tk`)

### Option 1 — GUI Mode (Recommended)
```bash
python main.py
```
- A window opens with the Islamabad map drawn on a canvas
- Select **Source** and **Destination** from the dropdowns
- Choose an **Algorithm** (or "Run ALL")
- Click **Find Route** → path highlights in orange, results appear in sidebar

### Option 2 — Console Mode
```bash
python main.py --console
```
Interactive text menu:
```
[1] Find Route (single algorithm)
[2] Compare ALL Algorithms
[3] Simulate Traffic
[4] Block / Unblock a Road
[5] Display Map
[6] Show Node List
[0] Exit
```

---

## 🗺 Map — Islamabad Nodes

| # | Node | Description |
|---|------|-------------|
| 1 | F-6 | Supermarket / Jinnah Market area |
| 2 | F-7 | Kohsar Market area |
| 3 | F-8 | Karachi Company |
| 4 | F-10 | F-10 Markaz |
| 5 | G-6 | Secretariat area |
| 6 | G-7 | Aabpara Market |
| 7 | G-8 | G-8 Markaz |
| 8 | G-10 | G-10 Markaz |
| 9 | G-11 | G-11 Markaz |
| 10 | H-8 | NUST area |
| 11 | Blue Area | CBD / Commercial hub |
| 12 | Centaurus | The Centaurus Mall |
| 13 | I-8 | I-8 Markaz |
| 14 | Rawal Lake | Rawal Lake Park |
| 15 | Shakar Parian | Shakar Parian Hills |

---

## 🧠 Algorithms Summary

| Algorithm | Optimal? | Complete? | Uses Heuristic? |
|-----------|----------|-----------|-----------------|
| BFS | ✗ (by cost) | ✓ | ✗ |
| DFS | ✗ | ✗ | ✗ |
| UCS | ✓ | ✓ | ✗ |
| A* | ✓ | ✓ | ✓ |
| Greedy BFS | ✗ | ✗ | ✓ |

---

## ✨ Bonus Features

| Feature | How to Use |
|---------|-----------|
| Traffic Simulation | Click **Simulate Traffic** (GUI) or menu option 3 (console) |
| Block Road | Click **Block Road Mode** then click 2 nodes (GUI) or menu option 4 (console) |
| Path Visualization | Automatically highlights path in orange (GUI) |

---

## 📊 Sample Output (Console)

```
[BFS]    Path: F-6 → G-6 → H-8 → Blue Area → Rawal Lake  | Cost: 14.00 km | Nodes: 13
[DFS]    Path: F-6 → G-6 → H-8 → Blue Area → Rawal Lake  | Cost: 14.00 km | Nodes: 7
[UCS]    Path: F-6 → G-6 → H-8 → Blue Area → Rawal Lake  | Cost: 14.00 km | Nodes: 15
[A*]     Path: F-6 → G-6 → H-8 → Blue Area → Rawal Lake  | Cost: 14.00 km | Nodes: 10
[Greedy] Path: F-6 → F-7 → G-7 → G-8 → Blue Area → Lake  | Cost: 17.60 km | Nodes: 6
```

---

## 👤 Author

Muhammad Ibrahim  
BS Artificial Intelligence — Semester 4  
Bahria University, Islamabad
