from itertools import zip_longest
from typing import TYPE_CHECKING
import os
import pygame
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text
from src.core import Drone

if TYPE_CHECKING:
    from src.visualizer._protocol import VisualizerProtocol
    from src.dijkstra import Dijkstra
    from src.core import DroneMap


class Simulation:
    """
    Manages the simulation logic and visualization for drones.

    This class coordinates drone movement, state snapshots, Pygame animations,
    and terminal output for capacity monitoring.
    """
    def __init__(
        self,
        d_map: "DroneMap",
        vis: "VisualizerProtocol",
        dijkstra: "Dijkstra",
        cap_info: bool = False
    ) -> None:
        """
        Initializes the simulation environment.

        Args:
            d_map: Object containing the map, zones, and drones.
            vis: Visualizer protocol for rendering.
            dijkstra: Pathfinding algorithm instance.
            cap_info: If True, prints the capacity table to the terminal.
        """
        self.d_map: "DroneMap" = d_map
        self.visualizer: "VisualizerProtocol" = vis
        self.dijkstra: "Dijkstra" = dijkstra
        self.cap_info: bool = cap_info
        self.turn_in_progress: bool = False
        self.manual_mode: bool = True
        self.paths: list[list[str]] = [[]]
        self.drone_pos: dict[int, tuple[float, float]] = {}
        self.turn_log: list[str] = []
        self.prev_zones: dict[str, tuple[int, int]] = {}
        self.prev_connections: dict[str, tuple[int, int]] = {}

    def _snapshot_state(self) -> None:
        """Captures a snapshot of current capacities before movement."""
        for name, (obj, _) in self.d_map.zones.items():
            self.prev_zones[name] = (obj.count_drones, obj.max_drones)

        for name, conn in self.d_map.connections.items():
            self.prev_connections[name] = (
                conn.curr_capacity, conn.max_link_capacity
            )

    def animate_drone(self, drone_id: int) -> None:
        """
        Calculates smooth drone position for the animation frame.

        Args:
            drone_id: Unique ID of the drone to animate.
        """
        v: "VisualizerProtocol" = self.visualizer
        d_data = self.d_map.drones.get(drone_id)
        if not d_data:
            return

        d_obj, d_rect = d_data
        dest_x: float = v.sx(d_obj.target_x)
        dest_y: float = v.sy(d_obj.target_y)

        # Initialize position if not present in history
        if drone_id not in self.drone_pos:
            self.drone_pos[drone_id] = (
                float(d_rect.centerx), float(d_rect.centery)
            )

        curr_x, curr_y = self.drone_pos[drone_id]
        dx, dy = dest_x - curr_x, dest_y - curr_y
        distance = (dx**2 + dy**2)**0.5
        step = 3.0

        if distance <= step:
            curr_x, curr_y = dest_x, dest_y
            d_obj.is_moving = False
        else:
            curr_x += (dx / distance) * step
            curr_y += (dy / distance) * step
            d_obj.is_moving = True

        self.drone_pos[drone_id] = (curr_x, curr_y)
        d_rect.center = (int(curr_x), int(curr_y))

    def build_info(self) -> None:
        """Generates and prints the capacity table using Rich."""
        console = Console()
        os.system("clear")

        if self.cap_info:
            table = Table(show_header=True, header_style="bold white")
            table.add_column("ZONE", width=30, header_style="bold cyan")
            table.add_column("CONNECTION", header_style="bold cyan")

            zones_txt, conns_txt = [], []

            # Process zone display logic
            for name, (obj, _) in self.d_map.zones.items():
                used, cap = obj.count_drones, obj.max_drones
                style = "bold red" if used >= cap and cap > 0 else \
                        "yellow" if used > 0 else "white"
                zones_txt.append(
                    Text(f"{name}: {used}/{cap} drones", style=style)
                )

            # Process connection display logic
            for name, conn in self.d_map.connections.items():
                used, cap = conn.curr_capacity, conn.max_link_capacity
                clean_name = "->".join(sorted(name.split('-')))
                style = "bold red" if used >= cap and cap > 0 else \
                        "yellow" if used > 0 else "white"
                conns_txt.append(
                    Text(f"{clean_name}: {used}/{cap} capacity", style=style)
                )

            for z, c in zip_longest(zones_txt, conns_txt, fillvalue=Text("")):
                table.add_row(z, c)

            console.print(table)

        for line in self.turn_log:
            rprint(line)

    def move_drones(self) -> list[str]:
        """Executes one step of movement for all eligible drones.

        Returns:
            list[str]: Log of moves formatted with Rich tags.
        """
        end_name = self.d_map.end_zone[0].name
        turn_moves = []

        for d_obj, _ in self.d_map.drones.values():
            if not d_obj.path or d_obj.is_moving:
                continue

            next_step = d_obj.path.pop(0)
            prev = d_obj.curr_zone

            # Decrement occupancy of current location (zone or link)
            if prev in self.d_map.zones:
                z_obj = self.d_map.zones[prev][0]
                z_obj.count_drones = max(0, z_obj.count_drones - 1)
            elif prev in self.d_map.connections:
                c_obj = self.d_map.connections[prev]
                c_obj.curr_capacity = max(0, c_obj.curr_capacity - 1)

            # Move to zones
            if next_step in self.d_map.zones:
                if next_step != d_obj.curr_zone:
                    nz, _ = self.d_map.zones[next_step]
                    nz.count_drones += 1
                    d_obj.target_x, d_obj.target_y = nz.x, nz.y
                    color = (
                        "blue"
                        if nz.zone_type.name.lower() == "restricted" else
                        "green"
                    )
                    turn_moves.append(
                        f"[bold {color}]D{d_obj.drone_id}-{next_step}"
                    )
                    if next_step == end_name:
                        d_obj.should_die = True
            # Move to connections
            else:
                conn = self.d_map.connections[next_step]
                conn.curr_capacity += 1
                z1, z2 = self.d_map.zones[conn.zone1][0], \
                    self.d_map.zones[conn.zone2][0]
                d_obj.target_x = (z1.x + z2.x)/2
                d_obj.target_y = (z1.y + z2.y)/2
                clean_c = "->".join(sorted(next_step.split('-')))
                turn_moves.append(f"[bold yellow]D{d_obj.drone_id}-{clean_c}")

            d_obj.curr_zone = next_step
            d_obj.is_moving = True

        return turn_moves

    def update(self) -> None:
        """Handles frame updates, animations, and turn transitions."""
        any_moving = False
        to_remove = []
        v = self.visualizer

        # Drone sprite animation cycle
        v.drone_frame_timer += 1
        if v.drone_frame_timer >= v.drone_frame_interval:
            v.drone_frame_timer = 0
            v.drone_frame_index = (v.drone_frame_index + 1) % \
                len(v.drone_frames)

        for d_id, (d_obj, _) in list(self.d_map.drones.items()):
            if d_obj.is_moving:
                self.animate_drone(d_id)
                any_moving = True
            elif getattr(d_obj, "should_die", False):
                to_remove.append(d_id)

        # Cleanup reached drones
        for d_id in to_remove:
            if d_id in self.d_map.drones:
                del self.d_map.drones[d_id]

        # Automatic turn logic
        if not any_moving and self.turn_in_progress:
            self.turn_in_progress = False
            if not self.manual_mode and self.d_map.drones:
                self.on_turn_request()

    def on_turn_request(self) -> None:
        """Requests a new logic turn if no drones are currently moving."""
        if any(d.is_moving for d, _ in self.d_map.drones.values()):
            return

        self.turn_in_progress = True
        self._snapshot_state()
        moves = self.move_drones()

        if moves:
            self.visualizer.turn_count += 1
            self.turn_log.append(
                f"[bold cyan]Turn {self.visualizer.turn_count}"
            )
            self.turn_log.append("[bold red] | [/bold red]".join(moves))
            self.turn_log.append("")
            self.build_info()
        else:
            self.turn_in_progress = False

    def reset(self) -> None:
        """Resets simulation state, drone counts, and pathfinding."""
        v = self.visualizer
        os.system("clear")
        v.turn_count = 0
        self.turn_in_progress = False
        self.drone_pos.clear()
        self.turn_log.clear()

        # Reset all occupancies
        for z in self.d_map.zones.values():
            z[0].count_drones = 0
        for c in self.d_map.connections.values():
            c.curr_capacity = 0

        # Initial positioning in start zone
        start = self.d_map.start_zone[0].name
        self.d_map.zones[start][0].count_drones = self.d_map.nb_drones
        self.d_map.drones.clear()

        for i in range(self.d_map.nb_drones):
            d_id = i + 1
            d_obj = Drone(drone_id=d_id)
            d_obj.curr_zone = start
            self.d_map.drones[d_id] = (d_obj, 0)

        self.dijkstra.reservations.clear()
        self.dijkstra.link_reservations.clear()
        self.dijkstra.solve()
        v.create_drones()

    def run(self, map_name: str = "Fly-in") -> None:
        """
        Main Pygame execution loop.

        Args:
            map_name: Title of the Pygame window.
        """
        v = self.visualizer
        v.setup_window()
        v.setup_assets()
        pygame.display.set_caption(map_name)

        # Initial sync of data for Turn 0
        start = self.d_map.start_zone[0].name
        self.d_map.zones[start][0].count_drones = self.d_map.nb_drones
        for d_obj, _ in self.d_map.drones.values():
            d_obj.curr_zone = start

        clock = pygame.time.Clock()
        running = True
        if self.cap_info:
            self.build_info()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_RIGHT:
                        self.on_turn_request()
                    if event.key == pygame.K_m:
                        self.manual_mode = not self.manual_mode
                        if not self.manual_mode and not self.turn_in_progress:
                            self.on_turn_request()
                    if event.key == pygame.K_r:
                        self.reset()

            self.update()
            v.screen.fill((50, 50, 50))
            if hasattr(v, "zones_layer"):
                v.screen.blit(v.zones_layer, (0, 0))
            v.draw_drones()
            v.draw_ui()
            v.draw_tooltip()
            pygame.display.flip()
            clock.tick(60)
