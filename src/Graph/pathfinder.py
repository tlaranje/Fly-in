from collections import deque
from src.Parsing.validators import DroneMap
from src.Graph.graph import Graph


class PathFinder:
    def __init__(self, graph: Graph, map_data: DroneMap) -> None:
        self.graph = graph
        self.start = map_data.start_hub.name
        self.end = map_data.end_hub.name

    def find_shortest_path(self) -> list[str]:
        de: deque[list[str]] = deque([[self.start]])
        visited: set[str] = {self.start}

        while de:
            path = de.popleft()
            curr = path[-1]

            if curr == self.end:
                return path

            for conn, _ in self.graph.all_connections[curr]:
                if conn not in visited:
                    visited.add(conn)
                    de.append(path + [conn])
        return []
