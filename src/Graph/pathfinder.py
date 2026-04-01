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
