from src.Parsing import DroneMap, Zone
from rich import print


class Graph:
    def __init__(self, map_data: DroneMap) -> None:
        self.map_data = map_data
        self.zones: dict[str, Zone] = {}
        self.all_connections: dict[str, list[tuple[str, int]]] = {}
        self.build(map_data)

    def build(self, map_data: DroneMap) -> None:
        self.add_zones(map_data)
        self.add_connections(map_data)

    def add_zones(self, map_data: DroneMap) -> None:
        all_zones = [map_data.start_hub, map_data.end_hub] + map_data.hubs
        for zone in all_zones:
            self.zones[zone.name] = zone
            self.all_connections[zone.name] = []

    def add_connections(self, map_data: DroneMap) -> None:
        for conn in map_data.connections:
            if conn.zone1 not in self.all_connections:
                print(f"[red]Zone1 missing:[/red] {conn.zone1}")
            if conn.zone2 not in self.all_connections:
                print(f"[red]Zone2 missing:[/red] {conn.zone2}")

            self.all_connections[conn.zone1].append(
                (conn.zone2, conn.max_link_capacity)
            )
            self.all_connections[conn.zone2].append(
                (conn.zone1, conn.max_link_capacity)
            )
