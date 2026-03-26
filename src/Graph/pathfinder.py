from src.Parsing import DroneMap
from src.Graph import Graph
import heapq
from rich import print


class PathFinder:
    def __init__(self, graph: Graph, map_data: DroneMap) -> None:
        self.graph = graph
        self.start = map_data.start_hub.name
        self.end = map_data.end_hub.name
    """
    - identificar zonas críticas
    - ordená‑las por capacidade
    - penalizar uma zona de cada vez
    - gerar um novo caminho
    - parar quando o caminho for diferente
    - Agora quero que tu próprio dês o primeiro passo.
    """

    def find_alternative_path(self) -> None:
        zone = self.graph.zones
        path: list[str] = self.find_best_path()
        cri_zones: list[tuple[str, int]] = sorted([
            (zone[z].name, zone[z].max_drones) for z in path[1:-1]
        ], key=lambda x: x[1])
        print(cri_zones)

    def find_best_path(self, penalized_zones=None) -> list[str]:
        dist: dict[str, float] = {}
        prev: dict[str, str | None] = {}
        pq: list[tuple[float, str]] = []
        path: list[str] = []
        penalty = 100

        prev = {zone: None for zone in self.graph.zones}
        dist = {zone: float("inf") for zone in self.graph.zones}
        dist[self.start] = 0

        heapq.heappush(pq, (0, self.start))
        while pq:
            cost, curr_zone = heapq.heappop(pq)

            if cost > dist[curr_zone]:
                continue

            for z, _ in self.graph.all_connections[curr_zone]:
                zone = self.graph.zones[z]

                if zone.zone_type == "blocked":
                    continue

                move_cost = 2 if zone.zone_type == "restricted" else 1
                if penalized_zones and z in penalized_zones:
                    move_cost += penalty

                new_cost = cost + move_cost

                if new_cost < dist[z]:
                    dist[z] = new_cost
                    prev[z] = curr_zone
                    heapq.heappush(pq, (new_cost, z))
        nz: str | None = self.end
        while nz is not None:
            path.append(nz)
            nz = prev[nz]
        path.reverse()
        return path
