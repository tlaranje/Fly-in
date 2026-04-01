from src.Simulation.visualizer import Visualizer
from src.Simulation.drone import Drone
from src.Graph import Graph, PathFinder
from rich import print
import os


class Simulation:
    def __init__(
            self, graph: Graph, visualizer: Visualizer, path_finder: PathFinder
    ) -> None:
        self.map_data = graph.map_data
        self.graph = graph
        self.visualizer = visualizer
        self.drones: list[Drone] = []
        self.link_usage: dict = {}
        self.path_finder = path_finder
        self.turn_in_progress = False
        self.manual_mode = True
        self.paths: list[list[str]] = [[]]

    def set_drones_paths(self) -> None:
        if not self.paths or not self.paths[0]:
            return

        nb = len(self.drones)
        paths = self.paths

        # drone_id -> índice do path (round-robin)
        assignments = [drone_id % len(paths) for drone_id in range(nb)]

        # schedule global único — todos os drones partilham a mesma tabela
        schedules = self.path_finder.schedule_all_drones_multi(paths, assignments)

        for drone in self.drones:
            drone.schedule = schedules[drone.drone_id]
            drone.schedule_index = 0
            path_idx = assignments[drone.drone_id]
            drone.path = paths[path_idx][1:]

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

        if on_complete:
            on_complete()
        if distance <= step:
            self.visualizer.canvas.move(drone.drone_tag, dx, dy)
            drone.is_moving = False
            return

        move_x = dx / distance * step
        move_y = dy / distance * step
        self.visualizer.canvas.move(drone.drone_tag, move_x, move_y)
        self.visualizer.root.after(
            16, lambda: self.animate_drone(drone, x, y, on_complete)
        )

    def move_drones(self, drones: list[Drone]) -> list[str]:
        current_turn = self.visualizer.turn_count

        # Filtra só os drones cujo próximo passo está agendado para este turno
        active = []
        for d in drones:
            if not d.schedule:
                active.append(d)
                continue
            idx = d.schedule_index
            if idx < len(d.schedule):
                _zone, scheduled_turn = d.schedule[idx]
                if current_turn >= scheduled_turn:
                    active.append(d)

        zone = self.graph.zones
        v = self.visualizer

        turn_moves: list[str] = []
        planned: list[tuple[Drone, str, bool]] = []

        # — FASE 1: decidir movimentos (usa `active`, não `drones`) —
        for d in active:
            if not d.curr_zone or (not d.path and not d.in_transit_to):
                continue

            # 2º turno de zona restricted
            if d.in_transit_to:
                planned.append((d, d.in_transit_to, True))
                continue

            if not d.path:
                continue

            next_zone = d.path[0]
            nz = zone[next_zone]

            if nz.zone_type == "blocked":
                continue

            if nz.zone_type == "restricted":
                turn_moves.append(
                    f"[bold yellow]D{d.drone_id}-"
                    f"{d.curr_zone}->{next_zone}[/bold yellow]"
                )
                d.in_transit_to = next_zone
            else:
                turn_moves.append(
                    f"[bold green]D{d.drone_id}-{next_zone}[/bold green]"
                )
                planned.append((d, next_zone, False))

        # — FASE 2: executar movimentos —
        end = self.graph.map_data.end_hub.name

        for d, next_zone, arriving_restricted in planned:
            assert d.curr_zone is not None
            nz = zone[next_zone]

            zone[d.curr_zone].count_drones -= 1
            nz.count_drones += 1
            d.curr_zone = next_zone
            d.schedule_index += 1
            d.path.pop(0)

            if arriving_restricted:
                turn_moves.append(
                    f"[green3]D{d.drone_id}-{next_zone}[/green3]"
                )
                d.in_transit_to = None

            cx = (nz.x - v.min_x) * v.scale + v.margin
            cy = (nz.y - v.min_y) * v.scale + v.margin

            if d.curr_zone == end:
                nz.count_drones -= 1

                def on_arrive(drone=d):
                    drone.is_moving = False
                    if drone in self.drones:
                        self.drones.remove(drone)

                self.animate_drone(d, cx, cy, on_complete=on_arrive)
            else:
                d.is_moving = True
                self.animate_drone(d, cx, cy)

        return turn_moves

    def wait_for_animations(self) -> None:
        any_moving = any(getattr(d, 'is_moving', False) for d in self.drones)

        if any_moving:
            self.visualizer.root.after(16, self.wait_for_animations)
        else:
            self.turn_in_progress = False
            if self.drones:
                if not self.manual_mode:
                    self.visualizer.root.after(
                        100, lambda: self.on_key_n(None)
                    )
            else:
                return

    def on_key_n(self, event: object):
        if self.turn_in_progress or len(self.drones) == 0:
            return

        self.turn_in_progress = True
        vis = self.visualizer

        self.link_usage = {}

        vis.turn_count += 1
        vis.title_label.config(text=f"Turn {vis.turn_count}")

        print(f"\n[bold cyan]Turn [/bold cyan]{vis.turn_count}")
        moves = self.move_drones(self.drones)
        if moves:
            print("[bold red] | [/bold red]".join(moves))
        self.wait_for_animations()

    def toggle_mode(self, event: object):
        self.manual_mode = not self.manual_mode

        if not self.manual_mode and not self.turn_in_progress:
            self.on_key_n(None)

    def step(self) -> None:
        if len(self.drones) == 0:
            return

        self.link_usage = {}
        self.wait_for_animations()

    def reset(self, event: object = None):
        v = self.visualizer
        os.system("clear")
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
        self.paths = self.path_finder.find_k_paths(k=10)
        self.set_drones_paths()

    def run(self) -> None:
        v = self.visualizer

        v.root.bind("m", self.toggle_mode)
        v.root.bind("n", self.on_key_n)
        v.root.bind("r", self.reset)

        v.draw_connections()
        v.draw_zones()

        self.drones += v.draw_drones()
        self.paths = self.path_finder.find_k_paths(k=10)
        self.set_drones_paths()
        v.root.after(500, self.step)
        v.root.mainloop()
