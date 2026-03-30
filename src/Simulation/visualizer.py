from src.Simulation.drone import Drone
from src.Graph import Graph
import tkinter as tk


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
        self.width = (self.max_x - self.min_x) * self.scale + self.margin * 2
        self.height = (self.max_y - self.min_y) * self.scale + self.margin * 2
        self.background_color = "#2b2b2b"
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.background_color,
            highlightthickness=0
        )
        self.canvas.pack()

        self.root.configure(bg=self.background_color)

        self.title_label = tk.Label(
            self.root,
            text="Turn 0",
            font=("TkHeadingFont", 23, "bold"),
            bg=self.background_color
        )
        self.title_label.pack(before=self.canvas)
        self.turn_count = 0

    def draw_zones(self) -> None:
        for zone in self.graph.zones.values():
            cx = (zone.x - self.min_x) * self.scale + self.margin
            cy = (zone.y - self.min_y) * self.scale + self.margin

            rec_id = self.canvas.create_oval(
                cx - 16, cy - 16,
                cx + 16, cy + 16,
                fill=zone.color or "grey"
            )
            self.canvas.create_text(
                cx, cy,
                font=("TkHeadingFont", 13, "bold"),
                text=zone.zone_type[0].upper(),
                fill="white"
            )
            zone.canva_id = rec_id

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
        colors = [
            "cyan", "lime", "magenta", "blue", "pink",
            "white", "coral", "turquoise", "salmon"
        ]
        drones: list[Drone] = []
        z = self.graph.zones["start"]
        i = 0
        cx = (z.x - self.min_x) * self.scale + self.margin
        cy = (z.y - self.min_y) * self.scale + self.margin

        while i < self.map_data.nb_drones:
            tag = f"drone_{i}"
            color = colors[i % len(colors)]

            radius_big = 10
            circle_id = self.canvas.create_oval(
                cx - radius_big, cy - radius_big,
                cx + radius_big, cy + radius_big,
                fill=color,
                tags=tag
            )
            offset = 2
            x1, y1, x2, y2 = self.canvas.coords(circle_id)
            x1 += offset
            x2 -= offset
            y1 += offset
            y2 -= offset
            corners = [
                (x1, y1),
                (x2, y1),
                (x1, y2),
                (x2, y2)
            ]

            radius_small = 5
            for j, (ccx, ccy) in enumerate(corners):
                self.canvas.create_oval(
                    ccx - radius_small, ccy - radius_small,
                    ccx + radius_small, ccy + radius_small,
                    fill=color,
                    tags=tag
                )
            d = Drone(i, z.name)
            d.drone_tag = tag
            d.canva_id = circle_id
            d.current_zone = z.name
            drones.append(d)
            i += 1

        return drones

    def run(self) -> None:
        self.draw_zones()
        self.draw_connections()
        self.root.mainloop()
