from src.Simulation.visualizer import Visualizer
from src.Simulation.drone import Drone
from src.Graph import Graph, PathFinder
from dataclasses import dataclass
from rich import print


@dataclass
class Position:
    x: float
    y: float


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
            d.path = self.path_finder.find_alternative_path()
            d.path.remove("start")

    def animate_drone(
            self, drone: Drone, x: float, y: float, on_complete=None
    ) -> None:
        coords = self.visualizer.canvas.coords(drone.canva_id)

        if not coords:
            return

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

    def coodrs(
            self, curr_zone: str, next_zone: str
    ) -> tuple[Position, Position, Position]:
        zone = self.graph.zones

        def get_coords(zone_name: str) -> Position:
            coords = self.visualizer.canvas.coords(zone[zone_name].canva_id)
            x = (coords[0] + coords[2]) / 2
            y = (coords[1] + coords[3]) / 2
            return Position(x, y)

        curr_pos = get_coords(curr_zone)
        next_pos = get_coords(next_zone)
        cx = (next_pos.x + curr_pos.x) / 2
        cy = (next_pos.y + curr_pos.y) / 2
        center_pos = Position(cx, cy)
        return (curr_pos, center_pos, next_pos)

    def move_drones(self, drones: list[Drone]) -> None:
        zone = self.graph.zones
        conns = self.graph.all_connections
        v = self.visualizer

        for d in drones[:]:
            if getattr(d, 'is_moving', False) or len(d.path) == 0:
                continue
            if d.in_transit:
                d.transit_remaining -= 1

                if d.transit_remaining == 1:
                    continue

                if d.transit_remaining == 0:
                    tx, ty = d.transit_target_coords
                    d.is_moving = True

                    def on_arrive(drone=d):
                        drone.in_transit = False
                        drone.current_zone = drone.transit_target
                        zone[drone.current_zone].count_drones += 1
                    d.current_zone = d.transit_target

                    self.animate_drone(d, tx, ty, on_complete=on_arrive)
                    continue
            assert d.current_zone is not None

            next_zone = d.path[0]
            if zone[next_zone].zone_type == "restricted":
                coords = self.coodrs(d.current_zone, next_zone)
                curr_pos, center_pos, next_pos = coords

                zone[d.current_zone].count_drones -= 1

                d.in_transit = True
                d.transit_remaining = 2
                d.transit_target = next_zone
                d.transit_target_coords = (next_pos.x, next_pos.y)
                d.path.pop(0)
                d.current_zone = None

                d.is_moving = True
                self.animate_drone(d, center_pos.x, center_pos.y)

                continue

            cap = next(
                (c for z, c in conns[d.current_zone] if z == next_zone), 1
            )
            link = tuple(sorted((d.current_zone, next_zone)))

            if self.link_usage.get(link, 0) >= cap or \
               zone[next_zone].count_drones >= zone[next_zone].max_drones:
                zone_counts = {
                    name: z.count_drones
                    for name, z in self.graph.zones.items()
                }
                new_path = self.path_finder.find_best_path(
                    p_zones=[next_zone],
                    start_zone=d.current_zone,
                    zone_counts=zone_counts,
                    link_usage=self.link_usage
                )

                if new_path and new_path[0] == d.current_zone:
                    new_path = new_path[1:]

                d.path = new_path
                continue

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
        if self.turn_in_progress or len(self.drones) == 0:
            return

        self.turn_in_progress = True
        vis = self.visualizer

        self.link_usage = {}

        vis.turn_count += 1
        vis.title_label.config(text=f"Turn {vis.turn_count}")

        self.move_drones(self.drones)
        for d in self.drones:
            if d.blocked and d.current_zone is not None:
                new_path = self.path_finder.find_best_path(
                    p_zones=[d.blocked_next],
                    start_zone=d.current_zone
                )
                if new_path and new_path[0] == d.current_zone:
                    new_path = new_path[1:]
                d.path = new_path
                d.blocked = False
        self.wait_for_animations()

    def toggle_mode(self, event):
        self.manual_mode = not self.manual_mode

        if not self.manual_mode and not self.turn_in_progress:
            self.on_key_n(None)

    def step(self) -> None:
        if len(self.drones) == 0:
            return

        self.link_usage = {}
        self.wait_for_animations()

    def reset(self, event=None):
        v = self.visualizer

        v.canvas.delete("all")

        v.turn_count = 0
        v.title_label.config(text="Turn 0")

        for zone in self.graph.zones.values():
            zone.count_drones = 0

        self.drones.clear()

        self.link_usage = {}

        self.turn_in_progress = False

        v.draw_connections()
        v.draw_zones()

        self.drones += v.draw_drones()
        self.set_drone_path(self.drones)

    def run(self) -> None:
        v = self.visualizer

        v.root.bind("m", self.toggle_mode)
        v.root.bind("n", self.on_key_n)
        v.root.bind("r", self.reset)

        v.draw_connections()
        v.draw_zones()

        self.drones += v.draw_drones()
        self.set_drone_path(self.drones)
        v.root.after(500, self.step)
        v.root.mainloop()
