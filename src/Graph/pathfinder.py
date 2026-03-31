from src.Parsing import DroneMap
from src.Graph import Graph
import heapq


class Dijkstra:
    def __init__(self, graph: Graph, map_data: DroneMap) -> None:
        self.graph = graph
        self.start = map_data.start_hub.name
        self.end = map_data.end_hub.name
        self.reservations: dict[tuple[str, int], int] = {}
        self.reservations_links: dict[tuple[str, int], int] = {}

    def _apply_reservations(self, path: list[str]) -> None:
        t = 0
        self.reservations[(path[0], 0)] = self.reservations.get((path[0], 0), 0) + 1

        for i in range(1, len(path)):
            prev_node = path[i - 1]
            curr_node = path[i]
            zone = self.graph.zones[curr_node]
            travel_time = 2 if zone.zone_type == "restricted" else 1
            t += travel_time

            self.reservations[(curr_node, t)] = self.reservations.get((curr_node, t), 0) + 1

            link = tuple(sorted((prev_node, curr_node)))
            key = (str(link), t)
            self.reservations_links[key] = self.reservations_links.get(key, 0) + 1

        for future in range(t + 1, t + 5):
            self.reservations[(path[-1], future)] = self.reservations.get((path[-1], future), 0) + 1

    def find_k_paths(self, k: int) -> list[list[str]]:
        self.reservations = {}
        self.reservations_links = {}
        paths = []

        for _ in range(k):
            path = self.find_best_path()
            if not path:
                paths.append([self.start])
                continue
            paths.append(path)
            self._apply_reservations(path)

        return paths

    def find_best_path(self) -> list[str]:
        pq = [(0, 0, self.start, [self.start])]
        visited = set()

        while pq:
            cost, t, curr, path = heapq.heappop(pq)

            if curr == self.end:
                return path

            if (curr, t) in visited:
                continue
            visited.add((curr, t))

            for neighbor, link_cap in self.graph.all_connections[curr]:
                zone = self.graph.zones[neighbor]

                if zone.zone_type == "blocked":
                    continue

                travel_time = 2 if zone.zone_type == "restricted" else 1
                arrival = t + travel_time

                occupied = self.reservations.get((neighbor, arrival), 0)
                if occupied >= zone.max_drones:
                    continue

                link = tuple(sorted((curr, neighbor)))
                link_key = (str(link), arrival)
                if self.reservations_links.get(link_key, 0) >= link_cap:
                    continue

                move_cost = 0.5 if zone.zone_type == "priority" else travel_time
                heapq.heappush(pq, (cost + move_cost, arrival, neighbor, path + [neighbor]))

            if self.reservations.get((curr, t + 1), 0) < self.graph.zones[curr].max_drones:
                heapq.heappush(pq, (cost + 1, t + 1, curr, path + [curr]))

        return []
