from src.Parsing import DroneMap
from src.Graph import Graph
import heapq


class PathFinder:
    def __init__(self, graph: Graph, map_data: DroneMap) -> None:
        self.graph = graph
        self.start = map_data.start_hub.name
        self.end = map_data.end_hub.name

    def find_alternative_path(self) -> list[str]:
        zone = self.graph.zones
        path1: list[str] = self.find_best_path()
        cri_zones = sorted(
            [(z, zone[z].max_drones) for z in path1[1:-1]],
            key=lambda x: x[1]
        )

        for name, cap in cri_zones:
            path2 = self.find_best_path(p_zones=[name])
            if path2 != path1:
                return path2
        return path1

    def find_best_path(
        self, start_zone=None, p_zones=None, zone_counts=None, link_usage=None
    ) -> list[str]:
        dist: dict[str, float] = {}
        prev: dict[str, str] = {}
        pq: list[tuple[float, str]] = []
        path: list[str] = []
        penalty = 100

        if start_zone is None:
            start = self.start
        else:
            start = start_zone

        prev = {zone: "" for zone in self.graph.zones}

        dist = {zone: float("inf") for zone in self.graph.zones}
        dist[start] = 0

        heapq.heappush(pq, (0, start))
        while pq:
            cost, curr_zone = heapq.heappop(pq)

            if cost > dist[curr_zone]:
                continue

            for z, _ in self.graph.all_connections[curr_zone]:
                zone = self.graph.zones[z]
                move_cost = 2 if zone.zone_type == "restricted" else 1

                if zone_counts and zone_counts.get(z, 0) >= zone.max_drones:
                    move_cost += penalty
                if p_zones and z in p_zones:
                    move_cost += penalty

                if zone.zone_type == "blocked":
                    continue

                if p_zones and z in p_zones:
                    move_cost += penalty

                new_cost = cost + move_cost

                if new_cost < dist[z]:
                    dist[z] = new_cost
                    prev[z] = curr_zone
                    heapq.heappush(pq, (new_cost, z))
        nz = self.end
        while nz is not None and nz != start:
            path.append(nz)
            nz = prev[nz]
        path.append(start)
        path.reverse()
        return path
