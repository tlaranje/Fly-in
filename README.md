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