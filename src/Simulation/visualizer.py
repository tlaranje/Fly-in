from src.Simulation.drone import Drone
from src.Graph import Graph
import tkinter as tk
import random


class Visualizer:
    def __init__(self, graph: Graph) -> None:
        self.map_data = graph.map_data
        self.root = tk.Tk()
        self.root.title("Fly-in")
        self.graph = graph
        self.scale = 64
        self.margin = 32
        self.min_x = min(zone.x for zone in graph.zones.values())
        self.min_y = min(zone.y for zone in graph.zones.values())
        self.max_x = max(zone.x for zone in graph.zones.values())
        self.max_y = max(zone.y for zone in graph.zones.values())
        width = (self.max_x - self.min_x) * self.scale + self.margin * 2
        height = (self.max_y - self.min_y) * self.scale + self.margin * 2
        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg="grey",
            highlightthickness=0
        )
        self.canvas.pack()

        self.root.configure(bg="grey")

        self.title_label = tk.Label(
            self.root, text="Turn 0", font=("Arial", 20, "bold"), bg="grey"
        )
        self.title_label.pack(before=self.canvas)
        self.turn_count = 0

    def draw_zones(self) -> None:
        for zone in self.graph.zones.values():
            cx = (zone.x - self.min_x) * self.scale + self.margin
            cy = (zone.y - self.min_y) * self.scale + self.margin
            self.canvas.create_rectangle(
                cx - 16, cy - 16,
                cx + 16, cy + 16,
                fill=zone.color or "black"
            )
        pass

    def draw_connections(self) -> None:
        for zone1, n in self.graph.all_connections.items():
            z1 = self.graph.zones[zone1]
            for zone2, _ in n:
                z2 = self.graph.zones[zone2]
                x1 = (z1.x - self.min_x) * self.scale + self.margin
                y1 = (z1.y - self.min_y) * self.scale + self.margin
                x2 = (z2.x - self.min_x) * self.scale + self.margin
                y2 = (z2.y - self.min_y) * self.scale + self.margin
                self.canvas.create_line(
                    x1, y1, x2, y2, width=3, fill="black"
                )
        pass

    def draw_drones(self) -> list[Drone]:
        colors = ["cyan", "lime"]
        drones: list[Drone] = []
        z = self.graph.zones["start"]
        i = 0
        cx = (z.x - self.min_x) * self.scale + self.margin
        cy = (z.y - self.min_y) * self.scale + self.margin

        while i < self.map_data.nb_drones:
            rect_id = self.canvas.create_rectangle(
                cx - 10, cy - 10,
                cx + 10, cy + 10,
                fill=random.choice(colors)
            )
            d = Drone(i, z.name)
            d.canva_id = rect_id
            d.current_zone = z.name
            drones.append(d)
            i += 1
        return drones

    def run(self) -> None:
        self.draw_connections()
        self.draw_zones()
        self.root.mainloop()
