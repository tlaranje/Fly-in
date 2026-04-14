from typing import Any, TYPE_CHECKING
from src.Parsing import Zone_Types as ZT
from rich import print
import heapq

if TYPE_CHECKING:
    from src.Parsing import DroneMap


class Dijkstra():
    def __init__(self, d_map: "DroneMap") -> None:
        self.d_map: "DroneMap" = d_map
        self.reservations: dict[tuple[str, int], int] = {}
        self.reservations_links: dict[tuple[str, int], int] = {}

    def is_link_available(self, zone1: str, zone2: str, turn: int) -> bool:

        key = "-".join(sorted([zone1, zone2]))
        conn = self.d_map.connections.get(key)

        assert conn is not None

        # self.reservations_links[(conn.name, turn)] = (
        #     self.reservations_links.get((conn.name, turn), 0) + 1
        # )

        link_usage = self.reservations_links.get((conn.name, turn), 0)
        return link_usage < conn.max_link_capacity

    def is_zone_available(self, zone: str, turn: int) -> bool:
        z = self.d_map.zones[zone]

        # self.reservations[(z.name, turn)] = (
        #     self.reservations.get((z.name, turn), 0) + 1
        # )

        zone_usage = self.reservations.get((z.name, turn), 0)
        return zone_usage < z.max_drones

    def solve(self) -> tuple[dict[int, list[str]], int]:
        start = self.d_map.start_zone.name
        end = self.d_map.end_zone.name
        path: list[str] = []
        total_turns: int = 0
        turns_result: dict[int, list[str]] = {}

        for (d_id, d) in self.d_map.drones.items():
            path = self.find_path(start, end, d_id)
            if path:
                d.path = path
                self.apply_reservations(path)
            else:
                turns_result[d_id] = [start]
                d.path = [start]

        for t in turns_result.values():
            if t:
                turns = len(t) - 1
                if turns > total_turns:
                    total_turns = turns

        return (turns_result, total_turns)

    def find_path(self, start: str, end: str, id: int) -> Any:
        pq: list[tuple[float, int, str, list[str]]] = [(0, 0, start, [start])]
        zone = self.d_map.zones
        visited = set()

        while pq:
            print(pq)
            cost, turn, curr_zone, path = heapq.heappop(pq)
            if curr_zone == end:
                return path

            if (curr_zone, turn) in visited:
                continue
            visited.add((curr_zone, turn))
            for conn in self.d_map.connections.values():
                z1 = conn.zone1
                z2 = conn.zone2

                if curr_zone not in (z1, z2):
                    continue

                next_zone = z2 if z1 == curr_zone else z1
                zone_type = zone[next_zone].zone_type

                if zone_type == ZT.BLOCKED:
                    continue

                travel_cost = zone[next_zone].zone_type.cost
                arrivel_turn = travel_cost + turn
                zone_cost = float(travel_cost)

                if not zone_type == ZT.PRIORITY:
                    zone_cost += 0.001

                zone_ok = self.is_zone_available(next_zone, arrivel_turn)

                if zone_type == ZT.RESTRICTED:
                    zone_ok = zone_ok and self.is_zone_available(
                        next_zone, arrivel_turn - 1
                    )

                link_ok = True
                for t in range(travel_cost):
                    if not self.is_link_available(z1, z2, turn + t + 1):
                        link_ok = False
                        break

                if zone_ok and link_ok:
                    if zone_type == ZT.RESTRICTED:
                        new_path = path + [conn.name, next_zone]
                    else:
                        new_path = path + [next_zone]
                    heapq.heappush(pq, (cost + zone_cost, arrivel_turn,
                                        next_zone, new_path))

            if self.is_zone_available(curr_zone, turn + 1):
                heapq.heappush(pq, (cost + 1, turn + 1, curr_zone,
                                    path + [curr_zone]))
        return None

    def get_connection_obj(self, identifier: str | tuple[str, str]) -> Any:
        """
        Retrieve a connection object by identifier or node pair.

        Args:
            identifier: Connection name or tuple of connected node names.

        Returns:
            The matching connection object, or None if not found.
        """

    def apply_reservations(self, path: list[str]) -> None:
        """
        Reserve nodes and links for a calculated path.

        Respects zone movement: normal/priority = 1 turn, restricted = 2 turns.

        Args:
            path: Path to reserve, as a list of node/connection names.

        Returns:
            None.
        """

    def output(self, all_results: dict[int, list[str]],
               path_file: str) -> None:
        """
        Write the simulation results to an output file.

        Args:
            all_results: Mapping of drone ids to their computed paths.
            path_file: Destination file path for the output.

        Returns:
            None.
        """
