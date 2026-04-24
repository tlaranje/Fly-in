# Peer Evaluation Scale
### Drone Pathfinding Simulation Project

---

## 1. Introduction

Remain polite, courteous, respectful and constructive throughout the evaluation process. The well-being of the community depends on it.

- Identify with the evaluated person any dysfunctions in their work. Take time to discuss and debate the problems identified.
- Consider that peers may have understood the project instructions differently — always keep an open mind and grade as honestly as possible.
- Pedagogy is valid only if peer-evaluation is conducted seriously.

---

## 2. Guidelines

- Only grade work that is in the student's or group's Git repository.
- Double-check that the repository belongs to the correct student/group; ensure `git clone` is used in an empty folder.
- Check carefully for malicious aliases that might fool you into evaluating something other than the official repository.
- Carefully verify that both the evaluating and evaluated students have reviewed any grading scripts.
- If the evaluating student has not completed this project, they must read the entire subject before the defence.
- Use flags to signal empty repositories, non-functioning programs, norm errors, or cheating (final grade 0, or -42 for cheating).
- No segfault or unexpected program termination is allowed during the defence — final grade becomes 0.
- You should never need to edit any file except the configuration file.
- Verify the absence of memory leaks. All heap-allocated memory must be freed before program exit.

---

## 3. Preliminaries

### Basics

The review is conducted in the presence of the graded learner(s). This is how everyone progresses: by interacting with others. The learner(s) must be present during the defence — if absent, the review cannot proceed. As soon as a core functionality is non-functional, the review stops.

### Work Submission

Only grade work in the learner's or group's Git repository. Check that only the requested files are available. If extra/unexpected files are present, the evaluation stops here.

### README.md Requirements

The repository must contain a `README.md` file at its root with all of the following:

- A **Description** section explaining the project's purpose and brief overview.
- An **Instructions** section with details about how to run the project.
- An **Algorithm explanation** section describing the pathfinding approach and design decisions.
- Documentation of **visual representation** features and how they enhance user experience.
- **Example input and expected output** demonstrating the program's functionality.

---

## 4. Project Structure & Requirements

### OOP

The project is completely object-oriented with proper class design and follows Python OOP best practices. Check for proper class separation, encapsulation, and inheritance where appropriate.

### Type Safety

The project is completely type-safe and passes mypy type checking without errors. Run `mypy .` in the project directory to verify. If mypy is not installed, check that type hints are present throughout the codebase.

### Graph Implementation

The graph implementation is custom-built without using forbidden libraries (such as `networkx`, `graphlib`, etc.). The learner should be able to explain how it works.


## 5. Parser Implementation

### Input Files *(≥ 4/5 requirements must pass)*

- Number of drones using `nb_drones: <number>` format
- Zone definitions with type prefixes (`start_hub:`, `end_hub:`, `hub:`)
- Connection definitions using `connection: <zone1>-<zone2>` format
- Optional metadata with defaults (`zone=normal`, `max_drones=1`)
- Comments starting with `#` are ignored

### Error Handling *(≥ 4/5 cases must be handled)*

- Malformed files (missing drone count, invalid format)
- Invalid zone types — should reject with clear error messages
- Missing `start_hub` or `end_hub` definitions
- Invalid capacity values (non-positive integers)
- Duplicate zone names or connections


## 6. Zone & Movement Mechanics

### Zone Occupancy Rules

- Zones respect `max_drones` capacity (default 1)
- Drones cannot enter zones that would exceed capacity
- Multiple drones can share start and end zones
- Capacity constraints are properly enforced during simulation

### Movement Costs

| Zone Type    | Cost   | Notes                     |
|--------------|--------|---------------------------|
| `normal`     | 1 turn | Default                   |
| `restricted` | 2 turns| Slower movement           |
| `priority`   | 1 turn | Preferred in pathfinding  |
| `blocked`    | —      | Inaccessible              |

### Connection Capacity

- Connections respect `max_link_capacity` defined in connection metadata (default 1)
- Multiple drones can traverse high-capacity connections simultaneously
- Connection capacity limits are enforced during movement

---

## 7. Visual Representation

- The program provides clear visual feedback (colored terminal output and/or graphical interface)
- Colors specified in zone metadata are used for visualization
- Visual representation enhances understanding of the simulation
- The visual system clearly shows drone positions and movements
- The implementation demonstrates meaningful visual feedback

---

## 8. Basic Functionality Tests

### Simple Scenarios *(≥ 4/5 must pass)*

- Single drone on a linear path
- Multiple drones using different paths
- Provided example maps from `attachments/`
- Output format: each line = one turn, format `D<ID>-<zone>` or `D<ID>-<connection>`
- Stationary drones are omitted from output

### Simulation Ends Correctly

The program must stop producing output once all drones have arrived at the end zone.

---

## 9. Pathfinding Algorithm

### Valid Path

The algorithm must find valid paths for:
- Simple linear maps
- Maps with multiple possible paths
- Maps with bottlenecks and capacity constraints
- Maps using different zone types

### Conflict Resolution

- Scenarios where drones compete for limited capacity
- Algorithm handles multiple drones simultaneously
- Capacity constraints prevent conflicts
- Turn-based movement with multi-turn zones (restricted)

---

## 10. Performance Benchmarks

> Reference targets are provided as optimization goals to help learners evaluate and tune their algorithms.

### Easy Maps *(avg. < 10 turns)*

| Map / Scenario   | Drones | Target Turns |
|------------------|--------|--------------|
| Linear path      | 2      | ≤ 6          |
| Simple fork      | 3      | ≤ 6          |
| Basic capacity   | 4      | ≤ 8          |

### Medium Maps *(avg. 10–30 turns)*

| Map / Scenario   | Drones | Target Turns |
|------------------|--------|--------------|
| Dead end trap    | 5      | ≤ 15         |
| Circular loop    | 6      | ≤ 20         |
| Priority puzzle  | 4      | ≤ 12         |

### Hard Maps *(avg. < 60 turns)*

| Map / Scenario      | Drones | Target Turns |
|---------------------|--------|--------------|
| Maze nightmare      | 8      | ≤ 45         |
| Capacity hell       | 12     | ≤ 60         |
| Ultimate challenge  | 15     | ≤ 35         |

---

## 11. Edge Cases & Error Handling

### Edge Cases *(≥ 4/5 must pass)*

- Single drone scenarios
- Maps with bottlenecks or limited capacity
- Disconnected graphs (should handle gracefully)
- Invalid connections between zones
- Zero or very high capacity values

### Error Messages

Error messages should be clear and informative for:
- Malformed files with new format requirements
- Missing `start_hub` or `end_hub` zones
- Invalid capacity values
- Disconnected graphs
- Invalid zone types or connections

---

## 12. Code Quality & Documentation

> ⚠️ This is not a failing requirement but contributes to overall quality.

- Code is well-structured and readable
- Proper use of object-oriented principles
- Appropriate comments and documentation
- Consistent coding style
- Visual representation code is well-integrated

---

## 13. Quick Live Coding Modification

Ask the reviewee to add a `--capacity-info` flag that displays capacity information during simulation.

**Expected usage:**
```bash
./main.py --capacity-info map.txt
```

**Expected output:** normal simulation output **plus** per-turn capacity usage:
```
Zone X: Y/Z drones, Connection A-B: Y/Z capacity used
```

The reviewee should locate the relevant parsing and output code, make necessary modifications, and demonstrate that it works with a test case — all within **10 minutes**.

---

## 14. Bonus Features

### Exceptional Performance

The algorithm meets or outperforms **all** reference targets across Easy, Medium, and Hard map categories (same targets as listed in Section 10).

### Challenger Map

The **Impossible Dream** map is solved and beats the reference record of **45 turns**.
