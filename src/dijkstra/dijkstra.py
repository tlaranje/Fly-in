from typing import Any, TYPE_CHECKING
from src.core import ZoneTypes as ZT
import heapq

if TYPE_CHECKING:
    from src.core import DroneMap


class Dijkstra():
    def __init__(self, d_map: "DroneMap") -> None:
        self.d_map: "DroneMap" = d_map
        self.reservations: dict[tuple[str, int], int] = {}
        self.reservations_links: dict[tuple[str, int], int] = {}

    def is_link_available(self, zone1: str, zone2: str, turn: int) -> bool:
        key = "-".join(sorted([zone1, zone2]))
        conn = self.d_map.connections.get(key)

        assert conn is not None

        link_usage = self.reservations_links.get((conn.name, turn), 0)
        return link_usage < conn.max_link_capacity

    def is_zone_available(self, zone: str, turn: int) -> bool:
        z, r = self.d_map.zones[zone]
        zone_usage = self.reservations.get((z.name, turn), 0)
        return zone_usage < z.max_drones

    def solve(self) -> tuple[dict[int, list[str]], int]:
        turns_result: dict[int, list[str]] = {}
        start = self.d_map.start_zone[0].name
        end = self.d_map.end_zone[0].name
        path: list[str] = []
        total_turns: int = 0

        for (d, d_rect) in self.d_map.drones.values():
            path = self.find_path(start, end, d.drone_id)
            if path:
                d.path = path[1:]
                self.apply_reservations(path)
                turns_result[d.drone_id] = path
            else:
                turns_result[d.drone_id] = [start]
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
                zone_type = zone[next_zone][0].zone_type

                if zone_type == ZT.BLOCKED:
                    continue

                travel_cost = zone[next_zone][0].zone_type.cost
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

    def apply_reservations(self, path: list[str]) -> None:
        start_zone = self.d_map.zones["start"][0]
        self.reservations[(start_zone.name, 0)] = (
            self.reservations.get((start_zone.name, 0), 0) + 1
        )
        turn = 0
        i = 1
        while i < len(path):
            prev_zone = path[i - 1]
            if path[i] in self.d_map.zones:
                next_name = path[i]
            else:
                if i + 1 >= len(path):
                    break
                next_name = path[i + 1]
                if next_name not in self.d_map.zones:
                    break
            next_zone = self.d_map.zones[next_name][0]
            move_cost = next_zone.zone_type.cost
            conn = self.d_map.connections.get(
                "-".join(sorted([prev_zone, next_name])), None
            )
            for s in range(move_cost):
                t = turn + 1 + s
                self.reservations[(next_name, t)] = (
                    self.reservations.get((next_name, t), 0) + 1)
                if conn:
                    key = (conn.name, t)
                    self.reservations_links[key] = (
                        self.reservations_links.get(key, 0) + 1)
            turn += move_cost
            if path[i] not in self.d_map.zones:
                i += 2
            else:
                i += 1

        arrival_name = self.d_map.zones[path[-1]][0].name
        for future_t in range(turn + 1, turn + 11):
            self.reservations[(arrival_name, future_t)] = (
                self.reservations.get((arrival_name, future_t), 0) + 1)
