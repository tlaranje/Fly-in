from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from src.core import DroneMap
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
        self.text_font = pygame.font.SysFont("Arial", 30, bold=True)
        self.tooltip_font = pygame.font.SysFont("Arial", 20, bold=False)
        self.HEIGHT = 60
        self.INFO_HEIGHT = 120

    def setup_window(self) -> None:
        d_map, scale, margin = self.d_map, self.scale, self.margin
        all_x = [z.x for z, _ in d_map.zones.values()]
        all_y = [z.y for z, _ in d_map.zones.values()]

        self.offset_x, self.offset_y = min(all_x), min(all_y)
        max_x, max_y = max(all_x), max(all_y)

        self.width = int((max_x - self.offset_x) * scale + margin * 2)
        self.height = (
            int((max_y - self.offset_y) * scale + margin * 2)
            + self.HEIGHT + self.INFO_HEIGHT
        )

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fly-in")

    def draw_tooltip(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        m_vec = pygame.Vector2(mouse_pos)
        lines = []

        for d_id, (d_obj, d_rect) in self.d_map.drones.items():
            if d_rect.collidepoint(mouse_pos):
                lines = [
                    f"DRONE {d_id}",
                    "Status: Active",
                    f"Current Zone: {d_obj.curr_zone}"
                ]
                break

        if not lines:
            radius = self.scale // 2.8
            for z_name, (z_obj, _) in self.d_map.zones.items():
                sx = (z_obj.x - self.offset_x) * self.scale + self.margin
                sy = (
                    (z_obj.y - self.offset_y) * self.scale
                    + self.margin + self.HEIGHT
                )
                if m_vec.distance_to((sx, sy)) <= radius:
                    lines = [
                        f"ZONE: {z_name}",
                        f"Type: {z_obj.zone_type.name_str}, "
                        f"Max_drones: {z_obj.max_drones}, "
                        f"Cost: {z_obj.zone_type.cost}, "
                        f"Priority: {z_obj.zone_type.priority}"
                    ]
                    break

        if not lines:
            for c_name, c_obj in self.d_map.connections.items():
                z1, _ = self.d_map.zones[c_obj.zone1]
                z2, _ = self.d_map.zones[c_obj.zone2]

                p1 = pygame.Vector2(
                    (z1.x - self.offset_x) * self.scale + self.margin,
                    (z1.y - self.offset_y) * self.scale
                    + self.margin + self.HEIGHT
                )
                p2 = pygame.Vector2(
                    (z2.x - self.offset_x) * self.scale + self.margin,
                    (z2.y - self.offset_y) * self.scale
                    + self.margin + self.HEIGHT
                )

                line_vec = p2 - p1
                if line_vec.length_squared() > 0:
                    t = (m_vec - p1).dot(line_vec) / line_vec.length_squared()
                    t = max(0, min(1, t))
                    if m_vec.distance_to(p1 + t * line_vec) < 8:
                        lines = [
                            f"LINK: {c_name}",
                            f"From: {c_obj.zone1}, To: {c_obj.zone2}",
                            f"Capacity: {c_obj.max_link_capacity}"
                        ]
                        break

        self.render_fixed_info_panel(lines)

    def render_fixed_info_panel(self, lines: list[str]) -> None:
        panel_rect = pygame.Rect(
            0, self.height - self.INFO_HEIGHT, self.width, self.INFO_HEIGHT
        )
        pygame.draw.rect(self.screen, (20, 20, 25), panel_rect)
        pygame.draw.line(
            self.screen, (60, 60, 80),
            (0, panel_rect.top), (self.width, panel_rect.top), 2
        )

        if not lines:
            lines = ["SYSTEM READY", "Hover elements for details"]

        padding = 15
        max_width = self.width - (padding * 2)
        curr_y = panel_rect.top + padding

        title_surf = self.text_font.render(lines[0], True, (100, 150, 255))
        self.screen.blit(title_surf, (padding, curr_y))
        curr_y += title_surf.get_height() + 8

        for ln in lines[1:]:
            words = ln.split(' ')
            current_line_text = ""

            for word in words:
                test_line = current_line_text + word + " "
                test_size = self.tooltip_font.size(test_line)[0]

                if test_size < max_width:
                    current_line_text = test_line
                else:
                    s = self.tooltip_font.render(
                        current_line_text, True, (200, 200, 200)
                    )
                    self.screen.blit(s, (padding, curr_y))
                    curr_y += s.get_height() + 2
                    current_line_text = word + " "

            if current_line_text:
                s = self.tooltip_font.render(
                    current_line_text, True, (200, 200, 200)
                )
                self.screen.blit(s, (padding, curr_y))
                curr_y += s.get_height() + 2

    def draw_ui(self) -> None:
        texto = f"Turn {self.turn_count}"
        text_surf = self.text_font.render(texto, True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(self.width // 2, self.HEIGHT // 2)
        )
        self.screen.blit(text_surf, text_rect)

    def setup_assets(self) -> None:
        raw_drone = pygame.image.load("imgs/drone.png").convert_alpha()
        d_size = (raw_drone.get_width() // 12, raw_drone.get_height() // 12)
        self.drone_img = pygame.transform.smoothscale(raw_drone, d_size)

        raw_zone = pygame.image.load("imgs/zone.png").convert_alpha()
        z_size = (raw_zone.get_width() // 15, raw_zone.get_height() // 15)
        self.zone_img = pygame.transform.smoothscale(raw_zone, z_size)

        self.zones_layer = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.draw_connections()
        self.draw_zones()
        self.create_drones()

    def create_drones(self) -> None:
        scale, margin = self.scale, self.margin
        start, _ = self.d_map.zones["start"]

        sx = (start.x - self.offset_x) * scale + margin
        sy = (start.y - self.offset_y) * scale + margin + self.HEIGHT

        for d_id, d_data in self.d_map.drones.items():
            d_obj = d_data[0]
            d_obj.curr_zone = "start"
            d_obj.target_x, d_obj.target_y = start.x, start.y
            rect = self.drone_img.get_rect(center=(sx, sy))
            self.d_map.drones[d_id] = (d_obj, rect)

    def get_pygame_color(self, color_str: str | None) -> pygame.Color:
        if color_str is None:
            return pygame.Color("gray")
        specials = {
            "rainbow": (255, 105, 180),
            "darkred": (139, 0, 0),
            "crimson": (220, 20, 60),
        }
        if color_str in specials:
            return pygame.Color(specials[color_str])
        try:
            return pygame.Color(color_str)
        except ValueError:
            return pygame.Color("gray")

    def draw_img(
        self, img: "Surface", layer: "Surface", center: tuple
    ) -> None:
        imagerect = img.get_rect(center=center)
        layer.blit(img, imagerect)

    def draw_connections(self) -> None:
        for _, c_obj in self.d_map.connections.items():
            z1, _ = self.d_map.zones[c_obj.zone1]
            z2, _ = self.d_map.zones[c_obj.zone2]

            p1 = (
                (z1.x - self.offset_x) * self.scale + self.margin,
                (z1.y - self.offset_y) * self.scale + self.margin + self.HEIGHT
            )
            p2 = (
                (z2.x - self.offset_x) * self.scale + self.margin,
                (z2.y - self.offset_y) * self.scale + self.margin + self.HEIGHT
            )

            pygame.draw.line(self.zones_layer, (35, 35, 35), p1, p2, width=6)
            pygame.draw.aaline(self.zones_layer, (80, 100, 120), p1, p2)

    def draw_zones(self) -> None:
        scale, margin = self.scale, self.margin
        radius = self.scale // 3

        for (z, _) in self.d_map.zones.values():
            sx = (z.x - self.offset_x) * scale + margin
            sy = (z.y - self.offset_y) * scale + margin + self.HEIGHT
            center = (sx, sy)

            draw_color = self.get_pygame_color(z.color)
            pygame.draw.circle(self.zones_layer, draw_color, center, radius)
            self.draw_img(self.zone_img, self.zones_layer, center)

    def draw_drones(self) -> None:
        for _, drone_data in self.d_map.drones.items():
            if drone_data[1] is not None:
                self.draw_img(
                    self.drone_img, self.screen, drone_data[1].center
                )
