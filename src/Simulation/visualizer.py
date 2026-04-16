from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from src.Parsing import DroneMap
    from pygame import Surface


class Visualizer:
    def __init__(self, d_map: "DroneMap") -> None:
        pygame.init()
        self.d_map = d_map
        self.scale = 80
        self.margin = 64
        self.width: int = 0
        self.height: int = 0
        self.drone_img: "Surface"
        self.zone_img: "Surface"
        self.zones_layer: "Surface"
        self.screen: "Surface"
        self.offset_x: float = 0
        self.offset_y: float = 0
        self.turn_count: int = 0

    def setup_assets(self) -> None:
        self.drone_img = pygame.image.load("imgs/drone.png").convert_alpha()
        self.zone_img = pygame.image.load("imgs/zone.png").convert_alpha()

        self.zones_layer = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )

        self.draw_connections()
        self.draw_zones()
        self.create_drones()

    def setup_window(self) -> None:
        d_map = self.d_map
        margin = self.margin
        scale = self.scale

        all_x = []
        all_y = []

        for z, _ in d_map.zones.values():
            all_x.append(z.x)
            all_y.append(z.y)

        self.offset_x, max_x = min(all_x), max(all_x)
        self.offset_y, max_y = min(all_y), max(all_y)

        self.width = int((max_x - self.offset_x) * scale + margin * 2)
        self.height = int((max_y - self.offset_y) * scale + margin * 2)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fly-in")

    def create_drones(self) -> None:
        scale = self.scale
        margin = self.margin

        start, z = self.d_map.zones["start"]
        screen_x = (start.x - self.offset_x) * scale + margin
        screen_y = (start.y - self.offset_y) * scale + margin

        for drone_id, drone_data in self.d_map.drones.items():
            drone_obj = drone_data[0]
            drone_obj.target_x = start.x
            drone_obj.target_y = start.y
            rect = self.drone_img.get_rect(center=(screen_x, screen_y))
            self.d_map.drones[drone_id] = (drone_obj, rect)

    def get_pygame_color(self, color_str: str | None) -> pygame.Color:
        if color_str is None:
            return pygame.Color("gray")

        special_colors = {
            "rainbow": (255, 105, 180),
            "darkred": (139, 0, 0),
            "crimson": (220, 20, 60),
        }

        if color_str in special_colors:
            return pygame.Color(special_colors[color_str])

        try:
            return pygame.Color(color_str)
        except ValueError:
            return pygame.Color("gray")

    def draw_img(
        self, img: "Surface", layer: "Surface", center: tuple, scale: int = 1
    ) -> None:
        if scale > 1:
            new_size = (img.get_width() // scale, img.get_height() // scale)
            img = pygame.transform.smoothscale(img, new_size)

        imagerect = img.get_rect()
        imagerect.center = center
        layer.blit(img, imagerect)

    def draw_connections(self):
        for conn_name, conn_obj in self.d_map.connections.items():
            z1_data = self.d_map.zones[conn_obj.zone1]
            z2_data = self.d_map.zones[conn_obj.zone2]

            z1 = z1_data[0]
            z2 = z2_data[0]

            start_pos = (
                (z1.x - self.offset_x) * self.scale + self.margin,
                (z1.y - self.offset_y) * self.scale + self.margin
            )
            end_pos = (
                (z2.x - self.offset_x) * self.scale + self.margin,
                (z2.y - self.offset_y) * self.scale + self.margin
            )

            pygame.draw.aaline(
                self.zones_layer, (100, 100, 100), start_pos, end_pos, 5
            )

    def draw_zones(self) -> None:
        scale = self.scale
        margin = self.margin
        radius = self.scale // 3

        for (z, r) in self.d_map.zones.values():
            screen_x = (z.x - self.offset_x) * scale + margin
            screen_y = (z.y - self.offset_y) * scale + margin
            center = (screen_x, screen_y)
            draw_color = self.get_pygame_color(z.color)
            pygame.draw.circle(
                self.zones_layer, draw_color, center, radius, width=0
            )
            self.draw_img(self.zone_img, self.zones_layer, center, 15)

    def draw_drones(self) -> None:
        for _, drone_data in self.d_map.drones.items():
            assert drone_data[1] is not None
            self.draw_img(
                self.drone_img, self.screen, drone_data[1].center, 12
            )
