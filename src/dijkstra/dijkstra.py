from typing import Any, TYPE_CHECKING
from src.core import ZoneTypes as ZT
import heapq

if TYPE_CHECKING:
    from src.core import DroneMap


class Dijkstra:
    """
    Time-expanded Dijkstra pathfinder for the drone routing simulation.

    Computes collision-free paths for every drone by tracking zone and
    link occupancy per turn.  Reservations are applied incrementally so
    that each successive drone routes around already-claimed slots.

    Attributes:
        d_map (DroneMap): The drone map containing zones, connections
            and the fleet.
        reservations (dict[tuple[str, int], int]): Maps
            ``(zone_name, turn)`` to the number of drones that have
            reserved that zone at that turn.
        link_reservations (dict[tuple[str, int], int]): Maps
            ``(connection_name, turn)`` to the number of drones that
            have reserved that link at that turn.
    """

    def __init__(self, d_map: "DroneMap") -> None:
        """
        Initialise the solver with the drone map.

        Args:
            d_map (DroneMap): Fully validated drone map to route drones
                across.
        """
        self.d_map: "DroneMap" = d_map

        # Zone occupancy counters: (zone_name, turn) -> drone count.
        self.reservations: dict[tuple[str, int], int] = {}

        # Link occupancy counters: (connection_name, turn) -> drone count.
        self.link_reservations: dict[tuple[str, int], int] = {}

    def _is_link_free(
        self, origin: str, destination: str, turn: int
    ) -> bool:
        """
        Check whether a connection has remaining capacity at a given turn.

        The connection key is built by sorting both endpoint names so the
        lookup is direction-independent.

        Args:
            origin (str): Name of the first zone endpoint.
            destination (str): Name of the second zone endpoint.
            turn (int): Simulation turn to check occupancy for.

        Returns:
            bool: ``True`` when the link has not yet reached its maximum
            capacity for that turn.
        """
        # Sort endpoints to obtain the canonical connection key.
        conn_key = "-".join(sorted([origin, destination]))
        conn = self.d_map.connections.get(conn_key)
        assert conn is not None, (
            f"Connection between '{origin}' and '{destination}' not found."
        )

        current_usage = self.link_reservations.get((conn.name, turn), 0)
        return current_usage < conn.max_link_capacity

    def _is_zone_free(self, zone_name: str, turn: int) -> bool:
        """
        Check whether a zone has remaining drone capacity at a given turn.

        Args:
            zone_name (str): Name of the zone to check.
            turn (int): Simulation turn to check occupancy for.

        Returns:
            bool: ``True`` when the zone has not yet reached its maximum
            drone capacity for that turn.
        """
        zone_obj, _ = self.d_map.zones[zone_name]
        current_usage = self.reservations.get((zone_obj.name, turn), 0)
        return current_usage < zone_obj.max_drones

    def _is_start_zone(self, zone_name: str) -> bool:
        """
        Return ``True`` when *zone_name* is the map's staging start zone.

        The start zone is treated as an unlimited waiting area, so drones
        may hold there regardless of the normal capacity limit.

        Args:
            zone_name (str): Zone name to test.

        Returns:
            bool: ``True`` when the zone is the staging start zone.
        """
        return zone_name == self.d_map.start_zone[0].name

    def solve(self) -> tuple[dict[int, list[str]], int]:
        """
        Compute collision-free paths for every drone in the fleet.

        Iterates over all drones in fleet order.  Each drone finds the
        shortest available path given the reservations already placed by
        previously processed drones.  Paths are stored back onto the
        drone objects (excluding the shared start zone) and recorded in
        the returned mapping.

        Returns:
            tuple[dict[int, list[str]], int]: A two-tuple of:

            - A ``dict`` mapping each drone ID to its full ordered path
              (including the start zone).
            - The total number of turns required by the longest path
              across the entire fleet.
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
                # Store the path on the drone, excluding the start zone
                # because the drone is already positioned there.
                drone_obj.path = computed_path[1:]
                self._apply_reservations(computed_path)
                fleet_paths[drone_obj.drone_id] = computed_path
            else:
                # No route found: park the drone at the start zone.
                fleet_paths[drone_obj.drone_id] = [start_name]
                drone_obj.path = [start_name]

        # Determine the overall simulation length from the longest path.
        for recorded_path in fleet_paths.values():
            turn_count = len(recorded_path) - 1
            if turn_count > max_turns:
                max_turns = turn_count

        return fleet_paths, max_turns

    def _find_path(self, start: str, end: str, drone_id: int) -> Any:
        """
        Run time-expanded Dijkstra from *start* to *end* for one drone.

        The priority queue holds tuples of the form:
            (accumulated_cost, current_turn, zone_name, path_so_far)

        At each step the drone may either:

        * **Advance** — move along any available connection to a
          neighbouring zone (cost equals the zone type travel cost).
        * **Wait** — remain in the current zone for one turn (cost +1),
          provided the zone has capacity *or* it is the start zone.

        RESTRICTED zones are handled by inserting an extra connection
        waypoint into the path so the visualiser can animate the drone
        through the link midpoint.

        PRIORITY zones receive a small cost bonus (``−0.001``) to
        break ties in favour of those routes when accumulated costs are
        otherwise equal.

        Args:
            start (str): Name of the start zone.
            end (str): Name of the destination zone.
            drone_id (int): Identifier of the drone being routed
                (reserved for future per-drone constraints).

        Returns:
            list[str] | None: An ordered list of zone/connection names
            representing the full path (including *start*), or ``None``
            when no route exists.
        """
        # Initial state: zero cost, turn 0, at the start zone.
        priority_queue: list[tuple[float, int, str, list[str]]] = [
            (0, 0, start, [start])
        ]
        zone_registry = self.d_map.zones

        # Visited set prevents reprocessing the same (zone, turn) state.
        visited: set[tuple[str, int]] = set()

        while priority_queue:
            accumulated_cost, current_turn, current_zone, current_path = (
                heapq.heappop(priority_queue)
            )

            # Destination reached — return the path immediately.
            if current_zone == end:
                return current_path

            # Skip states that have already been expanded.
            state = (current_zone, current_turn)
            if state in visited:
                continue
            visited.add(state)

            for conn in self.d_map.connections.values():
                zone1 = conn.zone1
                zone2 = conn.zone2

                # Skip connections that do not touch the current zone.
                if current_zone not in (zone1, zone2):
                    continue

                neighbour = zone2 if zone1 == current_zone else zone1
                neighbour_type = zone_registry[neighbour][0].zone_type

                # Blocked zones are never traversable.
                if neighbour_type == ZT.BLOCKED:
                    continue

                travel_cost = neighbour_type.cost
                arrival_turn = current_turn + travel_cost

                # Give PRIORITY zones a fractional cost advantage so
                # they are preferred when total costs are tied.
                edge_cost = float(travel_cost)
                if neighbour_type != ZT.PRIORITY:
                    edge_cost += 0.001

                # RESTRICTED zones require two consecutive free turns to
                # account for the extra waypoint step in the path.
                zone_free = self._is_zone_free(neighbour, arrival_turn)
                if neighbour_type == ZT.RESTRICTED:
                    zone_free = zone_free and self._is_zone_free(
                        neighbour, arrival_turn - 1
                    )

                # Every intermediate link turn between current and
                # arrival must also be unoccupied.
                link_free = all(
                    self._is_link_free(
                        zone1, zone2, current_turn + offset + 1
                    )
                    for offset in range(travel_cost)
                )

                if zone_free and link_free:
                    # RESTRICTED zones get an intermediate connection
                    # waypoint inserted for the visualiser.
                    if neighbour_type == ZT.RESTRICTED:
                        extended_path = (
                            current_path + [conn.name, neighbour]
                        )
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

            # Waiting at the start zone is always allowed regardless of
            # capacity — it acts as an unlimited staging area.
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

        # Exhausted all reachable states without finding the destination.
        return None

    def _apply_reservations(self, path: list[str]) -> None:
        """
        Mark all zone and link slots consumed by a computed path.

        Iterates the path and increments the occupancy counters for every
        ``(zone, turn)`` and ``(connection, turn)`` pair the drone will
        occupy.  Connection waypoints (strings that appear in
        ``d_map.connections`` rather than ``d_map.zones``) are detected
        and skipped — the real destination zone is the element that
        follows the waypoint.

        After the main loop, if the drone's final position is *not* the
        end zone (i.e. no route was found), two additional future turns
        are reserved to prevent other drones from entering that zone
        while the stuck drone occupies it.

        Args:
            path (list[str]): Full ordered path returned by
                :meth:`_find_path`, including the start zone and any
                connection waypoints.
        """
        elapsed_turns = 0
        step_index = 1

        while step_index < len(path):
            step = path[step_index]

            if step in self.d_map.zones:
                # Regular zone step: the previous element is always a zone.
                next_zone_name = step
                real_prev = path[step_index - 1]

                # If the previous element was a connection waypoint,
                # step back one more to find the real origin zone.
                if real_prev not in self.d_map.zones:
                    real_prev = path[step_index - 2]

                # Advance by 1 index position (no waypoint involved).
                advance = 1
            else:
                # Connection waypoint: the real destination is one ahead.
                if step_index + 1 >= len(path):
                    # Waypoint at the end of the path — malformed, stop.
                    break

                next_zone_name = path[step_index + 1]
                if next_zone_name not in self.d_map.zones:
                    # Destination after waypoint is not a zone — stop.
                    break

                real_prev = path[step_index - 1]
                if real_prev not in self.d_map.zones:
                    real_prev = path[step_index - 2]

                # Advance by 2 to consume both waypoint and destination.
                advance = 2

            next_zone_obj = self.d_map.zones[next_zone_name][0]
            move_cost = next_zone_obj.zone_type.cost

            # Build the canonical connection key from both zone names.
            conn_key = "-".join(sorted([real_prev, next_zone_name]))
            conn = self.d_map.connections.get(conn_key)

            # Reserve the zone and link for every turn of the move.
            for offset in range(move_cost):
                reserved_turn = elapsed_turns + 1 + offset

                # Increment zone occupancy for this turn.
                self.reservations[(next_zone_name, reserved_turn)] = (
                    self.reservations.get(
                        (next_zone_name, reserved_turn), 0
                    ) + 1
                )

                # Increment link occupancy for this turn (if link exists).
                if conn:
                    link_key = (conn.name, reserved_turn)
                    self.link_reservations[link_key] = (
                        self.link_reservations.get(link_key, 0) + 1
                    )

            elapsed_turns += move_cost
            step_index += advance

        arrival_zone_name = self.d_map.zones[path[-1]][0].name
        end_zone_name = self.d_map.end_zone[0].name

        if arrival_zone_name != end_zone_name:
            # Reserve two future turns so other drones route around this
            # stranded drone rather than entering its zone.
            for future_turn in range(
                elapsed_turns + 1, elapsed_turns + 3
            ):
                self.reservations[(arrival_zone_name, future_turn)] = (
                    self.reservations.get(
                        (arrival_zone_name, future_turn), 0
                    ) + 1
                )
