from src.visualizer._protocol import VisualizerProtocol
from typing import TYPE_CHECKING
from rich import print as rprint
from src.core import Drone
import pygame
import os

if TYPE_CHECKING:
    from src.dijkstra import Dijkstra
    from src.core import DroneMap


class Simulation:
    """
    Manages the drone simulation loop, turn logic and animation.

    Attributes:
        d_map: The drone map with zones, connections and drones.
        visualizer: The pygame visualizer used for rendering.
        dijkstra: The pathfinding solver instance.
        turn_in_progress: Whether a turn animation is currently running.
        manual_mode: If True, turns advance only on keypress (N key).
        link_usage: Tracks connection usage per turn (reserved for future use).
        paths: Stores computed paths for each drone.
    """

    def __init__(
        self,
        d_map: "DroneMap",
        vis: "VisualizerProtocol",
        dijkstra: "Dijkstra",
    ) -> None:
        """
        Initializes the simulation with a map, visualizer and solver.

        Args:
            d_map: Parsed drone map containing zones, connections, drones.
            vis: Visualizer instance responsible for rendering.
            dijkstra: Dijkstra solver with pre-computed paths.
        """
        self.d_map: "DroneMap" = d_map
        self.visualizer: "VisualizerProtocol" = vis
        self.dijkstra: "Dijkstra" = dijkstra
        self.turn_in_progress: bool = False
        self.manual_mode: bool = True
        self.link_usage: dict = {}
        self.paths: list[list[str]] = [[]]
        self.drone_pos: dict[int, tuple[float, float]] = {}

    def animate_drone(self, drone_id: int) -> None:
        v: "VisualizerProtocol" = self.visualizer
        d_data = self.d_map.drones.get(drone_id)
        if not d_data:
            return

        d_obj, d_rect = d_data

        dest_x: float = v.sx(d_obj.target_x)
        dest_y: float = v.sy(d_obj.target_y)

        # Inicializa posição float se ainda não existe
        if drone_id not in self.drone_pos:
            self.drone_pos[drone_id] = (
                float(d_rect.centerx), float(d_rect.centery)
            )

        curr_x, curr_y = self.drone_pos[drone_id]

        dx: float = dest_x - curr_x
        dy: float = dest_y - curr_y
        distance: float = (dx ** 2 + dy ** 2) ** 0.5

        step: float = 3.0  # podes usar float agora

        if distance <= step:
            curr_x, curr_y = dest_x, dest_y
            d_obj.is_moving = False
        else:
            curr_x += (dx / distance) * step
            curr_y += (dy / distance) * step
            d_obj.is_moving = True

        # Guarda float e só depois converte para o rect
        self.drone_pos[drone_id] = (curr_x, curr_y)
        d_rect.center = (int(curr_x), int(curr_y))

    def move_drones(self) -> list[str]:
        """
        Pops the next path step for every idle drone and starts movement.

        Handles two kinds of path entries:
        - Zone name: drone moves to that zone's world position.
        - Connection name: drone moves to the midpoint of the link
          (used for restricted zones that insert a waypoint).

        Returns:
            A list of rich-formatted strings describing each drone's move,
            ready to be printed to the console.
        """
        end_name: str = self.d_map.end_zone[0].name
        turn_moves: list[str] = []

        for d_obj, d_rect in self.d_map.drones.values():
            # Skip drones with no remaining path or that are still moving
            if not d_obj.path or d_obj.is_moving:
                continue

            next_step: str = d_obj.path.pop(0)
            if next_step in self.d_map.zones:
                # --- Move to a zone ---
                nz, _ = self.d_map.zones[next_step]
                d_obj.target_x = nz.x
                d_obj.target_y = nz.y
                d_obj.is_moving = True
                d_obj.curr_zone = next_step

                color: str = (
                    "blue"
                    if nz.zone_type.name.lower() == "restricted"
                    else "green"
                )
                turn_moves.append(
                    f"[bold {color}]D{d_obj.drone_id}-"
                    f"{next_step}[/bold {color}]"
                )

                # Mark drone for removal once it reaches the end zone
                if next_step == end_name:
                    d_obj.should_die = True

            elif next_step in self.d_map.connections:
                # --- Move to midpoint of a restricted connection ---
                conn = self.d_map.connections[next_step]
                z1, _ = self.d_map.zones[conn.zone1]
                z2, _ = self.d_map.zones[conn.zone2]

                d_obj.target_x = (z1.x + z2.x) / 2
                d_obj.target_y = (z1.y + z2.y) / 2
                d_obj.is_moving = True

                clean_conn: str = "->".join(sorted(next_step.split('-')))
                turn_moves.append(
                    f"[bold yellow]D{d_obj.drone_id}-"
                    f"{clean_conn}[/bold yellow]"
                )

        return turn_moves

    def update(self) -> None:
        """
        Per-frame update: advances animations and checks turn completion.

        Iterates all drones:
        - Animates moving drones.
        - Removes drones that have reached the end zone.
        - When no drone is moving, marks the turn as complete and
          optionally triggers the next turn (automatic mode).
        """
        any_moving: bool = False
        to_remove: list[int] = []

        v = self.visualizer

        v.drone_frame_timer += 1
        if v.drone_frame_timer >= v.drone_frame_interval:
            v.drone_frame_timer = 0
            v.drone_frame_index = (
                (v.drone_frame_index + 1) % len(v.drone_frames)
            )

        for d_id in list(self.d_map.drones.keys()):
            d_data = self.d_map.drones.get(d_id)
            if not d_data:
                continue

            d_obj, _ = d_data

            if d_obj.is_moving:
                self.animate_drone(d_id)
                any_moving = True
            elif getattr(d_obj, "should_die", False):
                to_remove.append(d_id)

        # Remove drones that have arrived at the end zone
        for d_id in to_remove:
            if d_id in self.d_map.drones:
                del self.d_map.drones[d_id]

        # All animations finished — close the turn
        if not any_moving and self.turn_in_progress:
            self.turn_in_progress = False
            # In automatic mode, immediately trigger the next turn
            if not self.manual_mode and self.d_map.drones:
                self.on_turn_request()

    def on_turn_request(self) -> None:
        """
        Triggers a new turn if no drone is currently animating.

        Advances each drone one step along its path, increments the
        turn counter and prints move information to the console.
        Does nothing when a turn is already in progress.
        """
        if any(d.is_moving for d, _ in self.d_map.drones.values()):
            return

        self.turn_in_progress = True
        moves: list[str] = self.move_drones()

        if moves:
            self.visualizer.turn_count += 1
            rprint(
                f"\n[bold cyan]Turn [/bold cyan]"
                f"{self.visualizer.turn_count}"
            )
            rprint("[bold red] | [/bold red]".join(moves))
        else:
            self.turn_in_progress = False

    def reset(self) -> None:
        """
        Resets the simulation to its initial state and re-runs Dijkstra.

        Clears all drone positions, reservations and the turn counter,
        then rebuilds the drone fleet and recomputes paths from scratch.
        """
        v: "VisualizerProtocol" = self.visualizer
        os.system("clear")

        v.turn_count = 0
        self.turn_in_progress = False
        self.drone_pos.clear()

        # Reset drone counters on every zone
        for zone_tuple in self.d_map.zones.values():
            zone_tuple[0].count_drones = 0

        # Rebuild drone fleet (IDs start at 1 after reset)
        self.d_map.drones.clear()
        for i in range(self.d_map.nb_drones):
            self.d_map.drones[i + 1] = (Drone(drone_id=i + 1), 0)

        # Clear old reservations and recompute paths
        self.dijkstra.reservations.clear()
        self.dijkstra.link_reservations.clear()
        self.dijkstra.solve()

        v.create_drones()

    def run(self) -> None:
        """
        Initializes the window and enters the main pygame event loop.

        Key bindings:
        - ``N``: advance one turn (manual mode).
        - ``M``: toggle manual / automatic mode.
        - ``R``: reset the simulation.
        - ``ESC`` / window close: exit.
        """
        v: "VisualizerProtocol" = self.visualizer
        v.setup_window()
        v.setup_assets()

        clock: pygame.time.Clock = pygame.time.Clock()
        running: bool = True

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
                        if (
                            not self.manual_mode
                            and not self.turn_in_progress
                        ):
                            self.on_turn_request()

                    if event.key == pygame.K_r:
                        self.reset()

            self.update()

            # --- Draw ---
            v.screen.fill((50, 50, 50))

            if hasattr(v, "zones_layer"):
                # Blit the pre-rendered static layer (zones + connections)
                v.screen.blit(v.zones_layer, (0, 0))

            v.draw_drones()
            v.draw_ui()
            v.draw_tooltip()

            pygame.display.flip()
            clock.tick(60)
