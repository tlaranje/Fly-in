from src.Simulation.visualizer import Visualizer
from src.Simulation.drone import Drone
from src.Graph import Graph, PathFinder


class Simulation:
    def __init__(
            self, graph: Graph, visualizer: Visualizer, path_finder: PathFinder
    ) -> None:
        self.map_data = graph.map_data
        self.graph = graph
        self.visualizer = visualizer
        self.drones: list[Drone] = []
        self.turns: list[str] = []
        self.link_usage: dict = {}
        self.path_finder = path_finder
        self.turn_in_progress = False
        self.manual_mode = True

    def set_drone_path(self, drones: list[Drone]) -> None:
        for d in drones:
            d.path = self.path_finder.find_best_path()
            d.path.remove("start")

    def animate_drone(
            self, drone: Drone, x: int, y: int, on_complete=None
    ) -> None:
        coords = self.visualizer.canvas.coords(drone.canva_id)
        cur_x = (coords[0] + coords[2]) / 2
        cur_y = (coords[1] + coords[3]) / 2
        dx = x - cur_x
        dy = y - cur_y
        distance = (dx**2 + dy**2) ** 0.5
        step = 5

        if distance <= step:
            self.visualizer.canvas.move(drone.canva_id, dx, dy)
            drone.is_moving = False
            if on_complete:
                on_complete()
            return

        move_x = dx / distance * step
        move_y = dy / distance * step
        self.visualizer.canvas.move(drone.canva_id, move_x, move_y)
        self.visualizer.root.after(
            16, lambda: self.animate_drone(drone, x, y, on_complete)
        )

    def move_drones(self, drones: list[Drone]) -> None:
        zone = self.graph.zones
        conns = self.graph.all_connections
        v = self.visualizer

        for d in drones[:]:
            if getattr(d, 'is_moving', False):
                continue
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

                    self.link_usage[link] = self.link_usage.get(link, 0) + 1
                    zone[d.current_zone].count_drones -= 1
                    zone[next_zone].count_drones += 1
                    d.current_zone = zone[next_zone].name
                    d.path.remove(next_zone)

                    d.is_moving = True

                    if d.current_zone in ["goal", "impossible_goal"]:
                        zone[d.current_zone].count_drones -= 1

                        def on_arrive(drone=d):
                            drone.is_moving = False
                            if drone in self.drones:
                                self.drones.remove(drone)
                        self.animate_drone(d, cx, cy, on_complete=on_arrive)
                    else:
                        self.animate_drone(d, cx, cy)

    def wait_for_animations(self) -> None:
        any_moving = any(getattr(d, 'is_moving', False) for d in self.drones)

        if any_moving:
            self.visualizer.root.after(16, self.wait_for_animations)
        else:
            self.turn_in_progress = False
            if not len(self.drones) == 0:
                if not self.manual_mode:
                    self.visualizer.root.after(
                        500, lambda: self.on_key_n(None)
                    )
            else:
                return

    def on_key_n(self, event):
        if self.turn_in_progress:
            return

        self.turn_in_progress = True
        vis = self.visualizer

        self.link_usage = {}

        vis.turn_count += 1
        vis.title_label.config(text=f"Turn {vis.turn_count}")

        self.move_drones(self.drones)

        self.wait_for_animations()

    def toggle_mode(self, event):
        self.manual_mode = not self.manual_mode

        if not self.manual_mode and not self.turn_in_progress:
            self.on_key_n(None)

    def step(self) -> None:
        v = self.visualizer

        if len(self.drones) == 0:
            return

        v.root.bind("m", self.toggle_mode)
        v.root.bind("n", self.on_key_n)

        self.link_usage = {}

        self.wait_for_animations()

    def run(self) -> None:
        v = self.visualizer

        v.draw_connections()
        v.draw_zones()

        self.drones += v.draw_drones()
        self.set_drone_path(self.drones)
        v.root.after(500, self.step)
        v.root.mainloop()
