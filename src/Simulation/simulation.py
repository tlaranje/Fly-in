from src.Simulation.visualizer import Visualizer
from src.Simulation.drone import Drone
from src.Graph import Graph


class Simulation:
    def __init__(self, graph: Graph, visualizer: Visualizer) -> None:
        self.map_data = graph.map_data
        self.graph = graph
        self.visualizer = visualizer
        self.drones: list[Drone] = []
        self.turns: list[str] = []
        self.visualizer.root.bind("n", self.on_key_n)
        self.visualizer.root.bind("N", self.on_key_n)

    def on_key_n(self, event):
        self.move_drones(self.drones)

    def move_drones(self, drones: list[Drone]) -> None:
        zone = self.graph.zones

        for d in drones:
            for c, _ in self.graph.all_connections[d.current_zone]:
                if zone[c].count_drones == 0:
                    v = self.visualizer
                    cx = (zone[c].x - v.min_x) * v.scale + v.margin
                    cy = (zone[c].y - v.min_y) * v.scale + v.margin
                    size = 10
                    self.visualizer.canvas.coords(
                        d.canva_id,
                        cx - size, cy - size,
                        cx + size, cy + size
                    )
                    d.current_zone = zone[c].name

    def run(self) -> None:
        self.visualizer.draw_connections()
        self.visualizer.draw_zones()

        zone = self.graph.zones
        while True:
            self.drones = self.visualizer.draw_drones()
            if zone["start"].max_drones == 1:
                break

        self.visualizer.root.mainloop()
