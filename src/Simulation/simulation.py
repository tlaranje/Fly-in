from typing import TYPE_CHECKING
from rich import print as rprint
import pygame
import os

if TYPE_CHECKING:
    from src.Simulation import Visualizer
    from src.dijkstra import Dijkstra
    from src.core import DroneMap


class Simulation:
    def __init__(
        self, d_map: "DroneMap", vis: "Visualizer", dijkstra: "Dijkstra"
    ) -> None:
        self.d_map = d_map
        self.visualizer = vis
        self.link_usage: dict = {}
        self.dijkstra = dijkstra
        self.turn_in_progress = False
        self.manual_mode = True
        self.paths: list[list[str]] = [[]]

    def animate_drone(self, drone_id: int) -> None:
        v = self.visualizer
        d_data = self.d_map.drones.get(drone_id)
        if not d_data:
            return

        d_obj, d_rect = d_data

        dest_x = (d_obj.target_x - v.offset_x) * v.scale + v.margin
        dest_y = (d_obj.target_y - v.offset_y) * v.scale + v.margin

        dx = dest_x - d_rect.centerx
        dy = dest_y - d_rect.centery
        distance = (dx**2 + dy**2) ** 0.5

        step = 5

        if distance <= step:
            d_rect.center = (dest_x, dest_y)
            d_obj.is_moving = False
        else:
            d_obj.is_moving = True
            d_rect.centerx += (dx / distance) * step
            d_rect.centery += (dy / distance) * step

    def move_drones(self) -> list[str]:
        ez = self.d_map.end_zone
        end_name = ez[0].name if isinstance(ez, (list, tuple)) else ez.name

        turn_moves: list[str] = []

        for d_obj, d_rect in self.d_map.drones.values():
            if not d_obj.path:
                continue

            if d_obj.is_moving:
                continue

            next_step = d_obj.path.pop(0)

            if next_step in self.d_map.zones:
                nz, _ = self.d_map.zones[next_step]
                d_obj.target_x = nz.x
                d_obj.target_y = nz.y
                d_obj.is_moving = True

                color = (
                    "blue" if nz.zone_type.name.lower() == "restricted"
                    else "green"
                )
                turn_moves.append(
                    f"[bold {color}]D{d_obj.drone_id}-"
                    f"{next_step}[/bold {color}]"
                )
                d_obj.curr_zone = next_step

                if next_step == end_name:
                    d_obj.should_die = True

            elif next_step in self.d_map.connections:
                conn = self.d_map.connections[next_step]
                z1, _ = self.d_map.zones[conn.zone1]
                z2, _ = self.d_map.zones[conn.zone2]

                d_obj.target_x = (z1.x + z2.x) / 2
                d_obj.target_y = (z1.y + z2.y) / 2
                d_obj.is_moving = True

                clean_conn = "->".join(sorted(next_step.split('-')))
                turn_moves.append(
                    f"[bold yellow]D{d_obj.drone_id}-"
                    f"{clean_conn}[/bold yellow]"
                )

        return turn_moves

    def update(self) -> None:
        any_moving = False
        to_remove = []

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

        for d_id in to_remove:
            if d_id in self.d_map.drones:
                del self.d_map.drones[d_id]

        if not any_moving and self.turn_in_progress:
            self.turn_in_progress = False
            if not self.manual_mode and self.d_map.drones:
                self.on_turn_request()

    def on_turn_request(self) -> None:
        if any(d.is_moving for d, _ in self.d_map.drones.values()):
            return

        self.turn_in_progress = True
        moves = self.move_drones()

        if moves:
            self.visualizer.turn_count += 1
            rprint(
                f"\n[bold cyan]Turn [/bold cyan]{self.visualizer.turn_count}"
            )
            rprint("[bold red] | [/bold red]".join(moves))
        else:
            self.turn_in_progress = False

    def reset(self) -> None:
        v = self.visualizer
        os.system("clear")

        v.turn_count = 0
        self.turn_in_progress = False

        for zone_tuple in self.d_map.zones.values():
            zone_tuple[0].count_drones = 0

        self.d_map.drones.clear()
        for i in range(self.d_map.nb_drones):
            from src.core import Drone
            self.d_map.drones[i + 1] = (Drone(drone_id=i + 1), 0)

        self.dijkstra.reservations.clear()
        self.dijkstra.reservations_links.clear()
        self.dijkstra.solve()

        v.create_drones()

    def run(self) -> None:
        v = self.visualizer
        v.setup_window()
        v.setup_assets()

        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
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
        pygame.quit()
