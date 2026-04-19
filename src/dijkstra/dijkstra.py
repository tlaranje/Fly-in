from typing import Any, TYPE_CHECKING
from src.core import ZoneTypes as ZT
import heapq

if TYPE_CHECKING:
    from src.core import DroneMap


class Dijkstra:
    """Time-expanded Dijkstra pathfinder for the drone routing simulation.

    Computes collision-free paths for every drone by tracking zone and
    link occupancy per turn.  Reservations are applied incrementally so
    that each successive drone routes around already-claimed slots.

    Attributes:
        d_map: The drone map containing zones, connections and the fleet.
        reservations: Maps (zone_name, turn) to the number of drones
            that have reserved that zone at that turn.
        link_reservations: Maps (connection_name, turn) to the number
            of drones that have reserved that link at that turn.
    """

    def __init__(self, d_map: "DroneMap") -> None:
        """Initialises the solver with the drone map.

        Args:
            d_map: Fully validated drone map to route drones across.
        """
        self.d_map: "DroneMap" = d_map
        self.reservations: dict[tuple[str, int], int] = {}
        self.link_reservations: dict[tuple[str, int], int] = {}

    # ------------------------------------------------------------------
    # Availability checks
    # ------------------------------------------------------------------

    def _is_link_free(self, origin: str, destination: str, turn: int) -> bool:
        """Checks whether a connection has capacity at a given turn.

        Args:
            origin: Name of the first zone endpoint.
            destination: Name of the second zone endpoint.
            turn: Simulation turn to check occupancy for.

        Returns:
            True when the link has not reached its maximum capacity.
        """
        conn_key = "-".join(sorted([origin, destination]))
        conn = self.d_map.connections.get(conn_key)
        assert conn is not None

        current_usage = self.link_reservations.get((conn.name, turn), 0)
        return current_usage < conn.max_link_capacity

    def _is_zone_free(self, zone_name: str, turn: int) -> bool:
        """Checks whether a zone has capacity at a given turn.

        Args:
            zone_name: Name of the zone to check.
            turn: Simulation turn to check occupancy for.

        Returns:
            True when the zone has not reached its drone capacity.
        """
        zone_obj, _ = self.d_map.zones[zone_name]
        current_usage = self.reservations.get((zone_obj.name, turn), 0)
        return current_usage < zone_obj.max_drones

    def _is_start_zone(self, zone_name: str) -> bool:
        """Returns True when zone_name is the map's start zone.

        Args:
            zone_name: Zone name to test.

        Returns:
            True when the zone is the staging start zone.
        """
        return zone_name == self.d_map.start_zone[0].name

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def solve(self) -> tuple[dict[int, list[str]], int]:
        """Computes paths for every drone and applies their reservations.

        Iterates over all drones in fleet order.  Each drone finds the
        shortest available path given the reservations already placed by
        previously processed drones.

        Returns:
            A two-tuple of:
            - A dict mapping drone ID to its full path (including start).
            - The total number of turns required by the longest path.
        """
        fleet_paths: dict[int, list[str]] = {}
        start_name = self.d_map.start_zone[0].name
        end_name = self.d_map.end_zone[0].name
        max_turns: int = 0

        for drone_obj, _ in self.d_map.drones.values():
            computed_path = self._find_path(
                start_name, end_name, drone_obj.drone_id
            )

            if computed_path:
                drone_obj.path = computed_path[1:]
                self._apply_reservations(computed_path)
                fleet_paths[drone_obj.drone_id] = computed_path
            else:
                fleet_paths[drone_obj.drone_id] = [start_name]
                drone_obj.path = [start_name]

        for recorded_path in fleet_paths.values():
            turn_count = len(recorded_path) - 1
            if turn_count > max_turns:
                max_turns = turn_count

        return fleet_paths, max_turns

    # ------------------------------------------------------------------
    # Core algorithm
    # ------------------------------------------------------------------

    def _find_path(self, start: str, end: str, drone_id: int) -> Any:
        """Runs time-expanded Dijkstra from start to end for one drone.

        The priority queue holds tuples of
        ``(accumulated_cost, current_turn, zone_name, path_so_far)``.

        A drone may wait in its current zone (cost +1, turn +1) or
        advance along any available connection.  Waiting at the start
        zone is always permitted regardless of capacity — it is a
        staging area shared by all drones simultaneously.

        RESTRICTED zones insert a connection waypoint into the path so
        the visualiser can animate the drone through the link midpoint.

        Args:
            start: Name of the start zone.
            end: Name of the end zone.
            drone_id: ID of the drone being routed.

        Returns:
            An ordered list of zone/connection names representing the
            full path, or None when no route exists.
        """
        priority_queue: list[tuple[float, int, str, list[str]]] = [
            (0, 0, start, [start])
        ]
        zone_registry = self.d_map.zones
        visited: set[tuple[str, int]] = set()

        while priority_queue:
            accumulated_cost, current_turn, current_zone, current_path = (
                heapq.heappop(priority_queue)
            )

            if current_zone == end:
                return current_path

            state = (current_zone, current_turn)
            if state in visited:
                continue
            visited.add(state)

            # --- Explore neighbouring zones via connections ---
            for conn in self.d_map.connections.values():
                zone1 = conn.zone1
                zone2 = conn.zone2

                if current_zone not in (zone1, zone2):
                    continue

                neighbour = zone2 if zone1 == current_zone else zone1
                neighbour_type = zone_registry[neighbour][0].zone_type

                # Blocked zones are never traversable.
                if neighbour_type == ZT.BLOCKED:
                    continue

                travel_cost = neighbour_type.cost
                arrival_turn = current_turn + travel_cost

                # Priority zones get a tiny cost bonus to rank them first
                # when accumulated costs are otherwise equal.
                edge_cost = float(travel_cost)
                if neighbour_type != ZT.PRIORITY:
                    edge_cost += 0.001

                # Restricted zones require two consecutive free turns
                # to account for the extra waypoint step.
                zone_free = self._is_zone_free(neighbour, arrival_turn)
                if neighbour_type == ZT.RESTRICTED:
                    zone_free = zone_free and self._is_zone_free(
                        neighbour, arrival_turn - 1
                    )

                # Every intermediate link turn must also be free.
                link_free = all(
                    self._is_link_free(zone1, zone2, current_turn + o + 1)
                    for o in range(travel_cost)
                )

                if zone_free and link_free:
                    if neighbour_type == ZT.RESTRICTED:
                        extended_path = current_path + [conn.name, neighbour]
                    else:
                        extended_path = current_path + [neighbour]

                    heapq.heappush(
                        priority_queue,
                        (
                            accumulated_cost + edge_cost,
                            arrival_turn,
                            neighbour,
                            extended_path,
                        ),
                    )

            # --- Wait option: stay in the current zone for one turn ---
            # FIX 1: The start zone is a shared staging area — waiting
            # there never consumes routing capacity regardless of the
            # zone's max_drones setting, so all drones can always queue.
            can_wait = (
                self._is_start_zone(current_zone)
                or self._is_zone_free(current_zone, current_turn + 1)
            )
            if can_wait:
                heapq.heappush(
                    priority_queue,
                    (
                        accumulated_cost + 1,
                        current_turn + 1,
                        current_zone,
                        current_path + [current_zone],
                    ),
                )

        return None

    # ------------------------------------------------------------------
    # Reservation management
    # ------------------------------------------------------------------

    def _apply_reservations(self, path: list[str]) -> None:
        """Marks all zone and link slots consumed by a computed path.

        Iterates the path and increments the occupancy counters for every
        (zone, turn) and (connection, turn) pair the drone will occupy.

        Three fixes applied vs the original implementation:

        FIX 1 (start zone not reserved at turn 0): The start zone is a
            shared staging area — all drones occupy it at turn 0
            simultaneously.  Reserving it per-drone would falsely block
            subsequent drones from waiting there.

        FIX 2 (real_prev resolution): When the previous path step is a
            connection waypoint rather than a zone name, we look one
            step further back to find the real previous zone, so the
            connection key lookup is always valid.

        FIX 3 (no end-zone buffer): The simulation removes a drone the
            moment it reaches the end zone, so no future turns need to
            be blocked there.  A small buffer is kept only for
            non-end intermediate arrivals (should not normally occur).

        Args:
            path: Full ordered path returned by ``_find_path``, including
                  the start zone and any connection waypoints.
        """
        elapsed_turns = 0
        step_index = 1

        while step_index < len(path):
            step = path[step_index]

            if step in self.d_map.zones:
                # Regular zone step.
                next_zone_name = step
                real_prev = path[step_index - 1]
                # FIX 2: skip back past any connection waypoint.
                if real_prev not in self.d_map.zones:
                    real_prev = path[step_index - 2]
                advance = 1
            else:
                # Connection waypoint — real destination is one ahead.
                if step_index + 1 >= len(path):
                    break
                next_zone_name = path[step_index + 1]
                if next_zone_name not in self.d_map.zones:
                    break
                real_prev = path[step_index - 1]
                if real_prev not in self.d_map.zones:
                    real_prev = path[step_index - 2]
                advance = 2

            next_zone_obj = self.d_map.zones[next_zone_name][0]
            move_cost = next_zone_obj.zone_type.cost

            # Build connection key from the two real zone names.
            conn_key = "-".join(sorted([real_prev, next_zone_name]))
            conn = self.d_map.connections.get(conn_key)

            # Reserve the zone and link for every turn of the move.
            for offset in range(move_cost):
                reserved_turn = elapsed_turns + 1 + offset
                self.reservations[(next_zone_name, reserved_turn)] = (
                    self.reservations.get(
                        (next_zone_name, reserved_turn), 0
                    ) + 1
                )
                if conn:
                    link_key = (conn.name, reserved_turn)
                    self.link_reservations[link_key] = (
                        self.link_reservations.get(link_key, 0) + 1
                    )

            elapsed_turns += move_cost
            step_index += advance

        # FIX 3: end zone needs no buffer — drone is removed immediately.
        # Keep a minimal buffer only for unexpected non-end arrivals.
        arrival_zone_name = self.d_map.zones[path[-1]][0].name
        end_zone_name = self.d_map.end_zone[0].name

        if arrival_zone_name != end_zone_name:
            for future_turn in range(elapsed_turns + 1, elapsed_turns + 3):
                self.reservations[(arrival_zone_name, future_turn)] = (
                    self.reservations.get(
                        (arrival_zone_name, future_turn), 0
                    ) + 1
                )
