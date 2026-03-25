from src.Simulation.visualizer import Visualizer
from src.Simulation.drone import Drone
from src.Graph import Graph, PathFinder
from rich import print
import math


class Simulation:
    def __init__(
            self, graph: Graph, visualizer: Visualizer, path_finder: PathFinder
    ) -> None:
        self.map_data = graph.map_data
        self.graph = graph
        self.visualizer = visualizer
        self.drones: list[Drone] = []
        self.turns: list[str] = []
        self.visualizer.root.bind("n", self.on_key_n)
        self.visualizer.root.bind("N", self.on_key_n)
        self.link_usage: dict = {}
        self.path_finder = path_finder

    def on_key_n(self, event):
        self.move_drones(self.drones)

    def set_drone_path(self, drones: list[Drone]) -> None:
        for d in drones:
            d.path = self.path_finder.find_shortest_path()
            d.path.remove("start")

    def move_drones(self, drones: list[Drone]) -> None:
        zone = self.graph.zones
        conns = self.graph.all_connections
        v = self.visualizer
        link_usage = self.link_usage
        size = 10

        for d in drones[:]:
            if len(d.path) == 0:
                continue
            next_zone = d.path[0]
            cap = next(
                (c for z, c in conns[d.current_zone] if z == next_zone), 1
            )
            link = tuple(sorted((d.current_zone, next_zone)))
            if self.link_usage.get(link, 0) >= cap:
                continue
            if zone[next_zone].count_drones < zone[next_zone].max_drones:
                if d.current_zone != "goal":
                    cx = (zone[next_zone].x - v.min_x) * v.scale + v.margin
                    cy = (zone[next_zone].y - v.min_y) * v.scale + v.margin
                    v.canvas.coords(
                        d.canva_id,
                        cx - size, cy - size,
                        cx + size, cy + size
                    )
                    link_usage[link] = link_usage.get(link, 0) + 1

                    zone[d.current_zone].count_drones -= 1
                    zone[next_zone].count_drones += 1

                    d.current_zone = zone[next_zone].name
                    d.path.remove(next_zone)
                    if d.current_zone in ["goal", "impossible_goal"]:
                        zone[d.current_zone].count_drones -= 1
                        self.drones.remove(d)

    def all_delivered(self) -> bool:
        return len(self.drones) == 0

    def step(self) -> None:
        vis = self.visualizer
        if len(self.drones) == 0:
            return
        self.move_drones(self.drones)
        self.link_usage = {}

        vis.turn_count += 1
        vis.title_label.config(text=f"Turn {vis.turn_count}")

        if not self.all_delivered():
            vis.root.after(500, self.step)
        else:
            print(len(self.drones))

    def run(self) -> None:
        self.visualizer.draw_connections()
        self.visualizer.draw_zones()

        self.drones += self.visualizer.draw_drones()
        self.set_drone_path(self.drones)
        self.visualizer.root.after(500, self.step)
        self.visualizer.root.mainloop()
