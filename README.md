*This project has been created as part of the 42 curriculum by \<tlaranje\>.*

# Fly-in

## Description

**Fly-in** is a drone routing simulation system built in Python. The goal is to move an entire fleet of drones from a central start zone to a target end zone in the fewest possible simulation turns, while respecting a strict set of movement, occupancy and capacity constraints.

The system reads a plain-text map file describing a weighted graph of zones and connections, computes collision-free paths for every drone using a **time-expanded Dijkstra algorithm**, and renders the simulation in real time through a **pygame graphical interface**.

Key features:
- Custom map parser supporting zone types, capacities and connection metadata
- Time-expanded Dijkstra pathfinding with zone and link reservation
- Animated pygame visualiser with hover tooltips and keybind panel
- Interactive main menu with difficulty-based map selection
- Manual and automatic turn progression modes


## Instructions

### Requirements

- Python 3.11 or later
- Dependencies listed in `pyproject.toml`

### Installation

```bash
make install
```

### Running

```bash
make run
```

## Usage

On launch, a menu window appears. Select **Play** to enter the map selection screen, choose a difficulty tier, then click a map to start the simulation.

### Keybinds (simulation window)

| Key | Action |
|-----|--------|
| `→` (Right Arrow) | Advance one turn (manual mode) |
| `M` | Toggle manual / automatic mode |
| `R` | Reset the simulation |
| `ESC` | Quit the simulation and return to menu |

### Hover tooltips

Move the mouse over any **zone**, **connection** or **drone** to see its properties in the bottom info panel.


## Map File Format

Maps are plain-text files placed under `maps/<difficulty>/`.

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub:   goal 10 10 [color=yellow]
hub: roof1     3 4 [zone=restricted color=red]
hub: roof2     6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB   7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]

connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

### Zone types

| Type | Movement cost | Notes |
|------|--------------|-------|
| `normal` | 1 turn | Default |
| `restricted` | 2 turns | Drone occupies the link during transit |
| `priority` | 1 turn | Preferred by the pathfinder when costs are tied |
| `blocked` | ∞ | Impassable — no drone may enter |

### Metadata options

- `zone=<type>` — zone routing type (default: `normal`)
- `color=<name>` — any pygame-compatible colour string (default: none)
- `max_drones=<n>` — maximum simultaneous occupancy (default: 1)
- `max_link_capacity=<n>` — maximum simultaneous drones on a connection (default: 1)


## Example Input and Expected Output

The following walkthrough uses the **Easy Level 2 — Simple Fork** map to illustrate how the parser, pathfinder and simulation interact end-to-end.

### Input map file (`maps/easy/02_simple_fork.txt`)

```
# Easy Level 2: Simple fork with two paths
nb_drones: 3

start_hub: start    0 0 [color=green]
hub:       junction 1 0 [color=yellow max_drones=2]
hub:       path_a   2  1 [color=blue]
hub:       path_b   2 -1 [color=blue]
end_hub:   goal     3 0 [color=red max_drones=3]

connection: start-junction
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

**What the parser produces:**

| Element | Details |
|---------|---------|
| Fleet | 3 drones (IDs 0, 1, 2), all spawned at `start` |
| Zones | `start`, `junction` (cap 2), `path_a`, `path_b`, `goal` (cap 3) |
| Connections | 5 undirected links, all with default capacity of 1 |

### Pathfinding result

Because `junction` only holds 2 drones at once and each connection carries 1 drone at a time, the time-expanded Dijkstra staggers departures automatically:

| Drone | Computed path | Arrival turn |
|-------|---------------|-------------|
| D0 | `start → junction → path_a → goal` | Turn 3 |
| D1 | `start → junction → path_a → goal` | Turn 4 |
| D2 | `start → junction → path_a → goal` | Turn 5 |

D1 waits one turn and D2 waits two turn at the start zone, because `junction` is fully reserved by D0 at turn 1 and is reserved by D1 at turn 2.

### Terminal output (with `--capacity-info`)

```
┌──────────────────────────────┬──────────────────────────────┐
│ ZONE                         │ CONNECTION                   │
├──────────────────────────────┼──────────────────────────────┘
│ start:    0/1 drones         │ junction->start:   0/1 cap   │
│ junction: 2/2 drones  (full) │ junction->path_a:  1/1 cap   │
│ path_a:   1/1 drones         │ junction->path_b:  1/1 cap   │
│ path_b:   1/1 drones         │ goal->path_a:      0/1 cap   │
│ goal:     0/3 drones         │ goal->path_b:      0/1 cap   │
└──────────────────────────────┴──────────────────────────────┘
Turn 1
D0-junction

Turn 2
D0-path_a | D1-junction

Turn 3
D0-goal | D1-path_a | D2-junction

Turn 4
D1-goal | D2-path_a

Turn 5
D2-goal
```

### Common error cases

If the map file is malformed the parser raises a descriptive `ValueError` before any simulation starts. Below are representative examples:

| Bad input | Error message |
|-----------|--------------|
| `nb_drones: 0` | `Map Error: nb_drones must be >= 1.` |
| Zone name `A-B` | `Map Error: Zone name 'A-B' can not have '-' in the name.` |
| `[color=red max_drones 2` (missing `=`) | `Map Error: Malformed metadata token 'max_drones 2'. Expected 'key=value'.` |
| Two zones at coordinates `(0, 0)` | `Map Error: Zones ['start', 'GhostZone'] share the same coordinates (0, 0).` |
| End zone unreachable from start | `Invalid map: No valid path found from 'S' to 'E'` |
| `max_link_capacity=0` | `Map Error: Connection 'S-E' capacity must be >= 1.` |


## Algorithm

### Time-expanded Dijkstra

The pathfinder operates on a **time-expanded graph** where each node is a `(zone, turn)` pair. This makes it possible to account for both spatial position and temporal conflicts in a single search.

**State representation**

```
(accumulated_cost, current_turn, zone_name, path_so_far)
```

**Per-drone routing**

Drones are routed one at a time in fleet order. After each drone finds its path, its zone and link occupancy is recorded as **reservations**. Subsequent drones plan around these reservations, naturally staggering their departures and choosing alternative routes when needed.

**Cost model**

- Normal / priority zone: `+1` turn per hop
- Restricted zone: `+2` turns per hop (drone occupies the link during both turns)
- PRIORITY zones receive a fractional cost bonus (`−0.001`) to break ties in their favour
- Waiting at the start zone is always free (unlimited staging area)

**Complexity**

For a graph with `Z` zones, `C` connections and a fleet of `D` drones routed over at most `T` turns:

- State space per drone: `O(Z × T)`
- Priority queue operations: `O(Z × T × log(Z × T))`
- Total across fleet: `O(D × Z × T × log(Z × T))`

Paths are computed once before the simulation starts and cached on each `Drone` object. No recalculation occurs at runtime unless the user resets (`R`).


## Visual Representation

The simulation window provides:

- **Static map layer** — zones rendered as coloured circles with an icon; connections as dark lines with a highlight overlay. This layer is pre-rendered once and blitted each frame for performance.
- **Animated drone sprites** — 16-frame sprite sheet animation; each drone moves smoothly toward its target using sub-pixel float positions converted to integer rect coordinates each frame.
- **Top bar** — current turn counter centred in a dedicated strip.
- **Bottom info panel** — split into two columns:
  - *Left*: live data for the hovered element (drone ID + zone, zone type + capacity + cost, or link capacity). Accent colour changes per element type.
  - *Right*: static keybind reference always visible.
- **Hover detection** — priority order: drone rects → zone circles → connection segments.

## Resources

### References

- pygame-ce documentation: https://pyga.me/docs/
- Pydantic v2 documentation: https://docs.pydantic.dev/latest/
- Python `heapq` module: https://docs.python.org/3/library/heapq.html

### AI Usage
- AI was used to assist in code formatting, documentation, and some bug fixes.