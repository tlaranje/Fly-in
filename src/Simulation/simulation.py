from typing import TYPE_CHECKING
from rich import print
import os

if TYPE_CHECKING:
    from src.Simulation.visualizer import Visualizer
    from src.Simulation.drone import Drone
    from src.Parsing import DroneMap
    from src.Graph import Dijkstra


class Simulation:
    def __init__(
            self, d_map: "DroneMap", vis: "Visualizer", dijkstra: "Dijkstra"
    ) -> None:
        self.d_map = d_map
        self.vis = vis
        self.link_usage: dict = {}
        self.dijkstra = dijkstra
        self.turn_in_progress = False
        self.manual_mode = True
        self.paths: list[list[str]] = [[]]

    def animate_drone(
        self, drone: "Drone", x: float, y: float, on_complete=None
    ) -> None:
        coords = self.vis.canvas.coords(drone.canva_id)
        if not coords:
            drone.is_moving = False
            return

        cur_x = (coords[0] + coords[2]) / 2
        cur_y = (coords[1] + coords[3]) / 2
        dx = x - cur_x
        dy = y - cur_y
        distance = (dx**2 + dy**2) ** 0.5
        step = 5

        if distance <= step:
            self.vis.canvas.move(drone.drone_tag, dx, dy)
            drone.is_moving = False
            if on_complete:
                on_complete()
            return

        move_x = dx / distance * step
        move_y = dy / distance * step
        self.vis.canvas.move(drone.drone_tag, move_x, move_y)
        self.vis.root.after(
            16, lambda: self.animate_drone(drone, x, y, on_complete)
        )

    def move_drones(self) -> list[str]:
        end = self.d_map.end_zone.name
        turn_moves: list[str] = []
        v = self.vis

        for (d_id, d) in list(self.d_map.drones.items()):
            if not d.path:
                continue

            next_step = d.path.pop(0)
            dest_x, dest_y = 0.0, 0.0

            if next_step in self.d_map.zones:
                nz = self.d_map.zones[next_step]
                dest_x = nz.x
                dest_y = nz.y

                color = (
                    "blue"
                    if nz.zone_type.name.lower() == "restricted" else
                    "green"
                )
                turn_moves.append(
                    f"[bold {color}]D{d.drone_id}-{next_step}[/bold {color}]"
                )
                d.curr_zone = next_step

            elif next_step in self.d_map.connections:
                conn = self.d_map.connections[next_step]
                z1 = self.d_map.zones[conn.zone1]
                z2 = self.d_map.zones[conn.zone2]

                dest_x = (z1.x + z2.x) / 2
                dest_y = (z1.y + z2.y) / 2
                turn_moves.append(
                    f"[bold yellow]D{d.drone_id}-"
                    f"{"->".join(sorted(next_step.split('-')))}[/bold yellow]"
                )

            cx = (dest_x - v.min_x) * v.scale + v.margin
            cy = (dest_y - v.min_y) * v.scale + v.margin

            if next_step == end:
                def on_arrive(drone=d):
                    drone.is_moving = False
                    if drone.drone_id in self.d_map.drones:
                        del self.d_map.drones[drone.drone_id]
                        self.vis.canvas.delete(drone.drone_tag)

                d.is_moving = True
                self.animate_drone(d, cx, cy, on_complete=on_arrive)
            else:
                d.is_moving = True
                self.animate_drone(d, cx, cy)

        return turn_moves

    def wait_for_animations(self) -> None:
        drones_list = list(self.d_map.drones.values())
        any_moving = any(getattr(d, 'is_moving', False) for d in drones_list)

        if any_moving:
            self.vis.root.after(16, self.wait_for_animations)
        else:
            self.turn_in_progress = False
            if self.d_map.drones:
                if not self.manual_mode:
                    self.vis.root.after(100, lambda: self.on_key_n(None))

    def on_key_n(self, event: object):
        if self.turn_in_progress:
            return

        if len(self.d_map.drones) == 0:
            return

        self.turn_in_progress = True
        self.link_usage = {}

        moves = self.move_drones()

        if moves:
            vis = self.vis
            vis.turn_count += 1
            vis.title_label.config(text=f"Turn {vis.turn_count}")
            print(f"\n[bold cyan]Turn [/bold cyan]{vis.turn_count}")
            print("[bold red] | [/bold red]".join(moves))
            self.wait_for_animations()
        else:
            self.turn_in_progress = False

    def toggle_mode(self, event: object):
        self.manual_mode = not self.manual_mode

        if not self.manual_mode and not self.turn_in_progress:
            self.on_key_n(None)

    def step(self) -> None:
        if len(self.d_map.drones) == 0:
            return

        if not self.manual_mode:
            self.on_key_n(None)
        else:
            self.wait_for_animations()

    def reset(self, event: object = None):
        v = self.vis
        os.system("clear")
        v.canvas.delete("all")

        v.turn_count = 0
        v.title_label.config(text="Turn 0")

        for zone in self.d_map.zones.values():
            zone.count_drones = 0

        self.d_map.drones.clear()

        self.link_usage = {}

        self.turn_in_progress = False

        v.draw_connections()
        v.draw_zones()

        v.draw_drones()

    def run(self) -> None:
        v = self.vis

        v.root.bind("m", self.toggle_mode)
        v.root.bind("n", self.on_key_n)
        v.root.bind("r", self.reset)

        v.draw_connections()
        v.draw_zones()
        v.draw_drones()

        for (_, d) in self.d_map.drones.items():
            if d.path and d.path[0] == d.curr_zone:
                d.path.pop(0)

        v.root.after(500, self.step)
        v.root.mainloop()
