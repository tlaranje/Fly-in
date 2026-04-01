from src.Parsing import DroneMap
from src.Graph import Graph
import heapq


class PathFinder:
    def __init__(self, graph: Graph, map_data: DroneMap) -> None:
        self.graph = graph
        self.start = map_data.start_hub.name
        self.end = map_data.end_hub.name

    def find_k_paths(self, k=3) -> list[list[str]]:
        paths = []

        zone_usage: dict[str, int] = {}
        zone_penalty: dict[str, int] = {}

        for _ in range(k):
            path = self.find_best_path(
                zone_usage=zone_usage,
                zone_penalty=zone_penalty
            )

            if not path or path in paths:
                break

            paths.append(path)

            for z in path[1:-1]:
                zone_usage[z] = zone_usage.get(z, 0) + 1
                zone_penalty[z] = zone_penalty.get(z, 0) + 2

        return paths

    def find_best_path(
        self,
        start_zone=None,
        p_zones=None,
        zone_usage=None,
        zone_penalty=None
    ) -> list[str]:

        dist: dict[str, float] = {}
        prev: dict[str, str | None] = {}
        pq: list[tuple[float, str]] = []
        path: list[str] = []

        penalty = 2

        start = start_zone if start_zone else self.start

        prev = {zone: None for zone in self.graph.zones}
        dist = {zone: float("inf") for zone in self.graph.zones}
        dist[start] = 0

        heapq.heappush(pq, (0, start))

        while pq:
            cost, curr_zone = heapq.heappop(pq)

            if cost > dist[curr_zone]:
                continue

            for z, _ in self.graph.all_connections[curr_zone]:
                zone = self.graph.zones[z]

                if zone.zone_type == "blocked":
                    continue

                move_cost = 2 if zone.zone_type == "restricted" else 1

                if zone_usage and zone_usage.get(z, 0) >= zone.max_drones:
                    move_cost += penalty

                if zone_penalty and z in zone_penalty:
                    move_cost += zone_penalty[z]

                if p_zones and z in p_zones:
                    move_cost += penalty

                new_cost = cost + move_cost

                if new_cost < dist[z]:
                    dist[z] = new_cost
                    prev[z] = curr_zone
                    heapq.heappush(pq, (new_cost, z))

        nz: str | None = self.end

        if nz is None:
            return []

        if prev[nz] is None and nz != start:
            return []

        while nz is not None:
            path.append(nz)
            nz = prev[nz]

        path.reverse()
        return path

    def schedule_all_drones_multi(
        self,
        paths: list[list[str]],
        drone_path_assignments: list[int],  # drone_id -> índice do path
    ) -> list[list[tuple[str, int]]]:
        """
        Schedule global: todos os drones partilham a mesma tabela de reservas.
        drone_path_assignments[i] = índice do path para o drone i
        """
        zone_turns: dict[str, dict[int, int]] = {
            z: {} for z in self.graph.zones
        }
        nb_drones = len(drone_path_assignments)
        schedules: list[list[tuple[str, int]]] = []

        for drone_id in range(nb_drones):
            path_idx = drone_path_assignments[drone_id]
            path = paths[path_idx]
            schedule: list[tuple[str, int]] = []
            current_turn = 0

            for zone_name in path[1:]:
                zone = self.graph.zones[zone_name]
                move_cost = 2 if zone.zone_type == "restricted" else 1

                while True:
                    slots = range(current_turn, current_turn + move_cost)
                    full = any(
                        zone_turns[zone_name].get(t, 0) >= zone.max_drones
                        for t in slots
                    )
                    if not full:
                        break
                    current_turn += 1

                for t in range(current_turn, current_turn + move_cost):
                    zone_turns[zone_name][t] = zone_turns[zone_name].get(t, 0) + 1

                schedule.append((zone_name, current_turn))
                current_turn += move_cost

            schedules.append(schedule)

        return schedules
