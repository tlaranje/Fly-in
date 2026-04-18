from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from src.core import DroneMap
    from pygame import Surface


class Visualizer:
    MIN_WIDTH = 520

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
        self.center_offset_x: int = 0
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

        map_width = int((max_x - self.offset_x) * scale + margin * 2)
        self.width = max(self.MIN_WIDTH, map_width)

        self.center_offset_x = (self.width - map_width) // 2

        self.height = (
            int((max_y - self.offset_y) * scale + margin * 2)
            + self.HEIGHT + self.INFO_HEIGHT
        )

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fly-in")

    def _sx(self, world_x: float) -> float:
        """World X -> screen X, accounting for centering."""
        return (
            (world_x - self.offset_x) * self.scale
            + self.margin + self.center_offset_x
        )

    def _sy(self, world_y: float) -> float:
        """World Y -> screen Y."""
        return (
            (world_y - self.offset_y) * self.scale
            + self.margin + self.HEIGHT
        )

    def draw_tooltip(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        m_vec = pygame.Vector2(mouse_pos)
        lines = []

        for d_id, (d_obj, d_rect) in self.d_map.drones.items():
            if d_rect.collidepoint(mouse_pos):
                lines = [
                    f"DRONE {d_id}",
                    f"Drone id: {d_id}",
                    f"Current Zone: {d_obj.curr_zone}"
                ]
                break

        if not lines:
            radius = self.scale // 2.8
            for z_name, (z_obj, _) in self.d_map.zones.items():
                sx = self._sx(z_obj.x)
                sy = self._sy(z_obj.y)
                if m_vec.distance_to((sx, sy)) <= radius:
                    lines = [
                        f"ZONE: {z_name}",
                        f"Type: {z_obj.zone_type.name_str} | "
                        f"Max_drones: {z_obj.max_drones}",
                        f"Cost: {z_obj.zone_type.cost} | "
                        f"Priority: {z_obj.zone_type.priority}"
                    ]
                    break

        if not lines:
            for c_name, c_obj in self.d_map.connections.items():
                z1, _ = self.d_map.zones[c_obj.zone1]
                z2, _ = self.d_map.zones[c_obj.zone2]

                p1 = pygame.Vector2(self._sx(z1.x), self._sy(z1.y))
                p2 = pygame.Vector2(self._sx(z2.x), self._sy(z2.y))

                line_vec = p2 - p1
                if line_vec.length_squared() > 0:
                    t = (
                        (m_vec - p1).dot(line_vec)
                        / line_vec.length_squared()
                    )
                    t = max(0, min(1, t))
                    if m_vec.distance_to(p1 + t * line_vec) < 8:
                        lines = [
                            f"LINK: {c_name}",
                            f"From: {c_obj.zone1} | To: {c_obj.zone2}",
                            f"Capacity: {c_obj.max_link_capacity}"
                        ]
                        break

        self.render_fixed_info_panel(lines)

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Word-wrap *text* into lines that fit within *max_width* pixels."""
        words = text.split(' ')
        wrapped: list[str] = []
        current = ""

        for word in words:
            test = (current + " " + word).strip()
            if self.tooltip_font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    wrapped.append(current)
                if self.tooltip_font.size(word)[0] > max_width:
                    while (
                        word
                        and self.tooltip_font.size(word + "…")[0] > max_width
                    ):
                        word = word[:-1]
                    word = word + "…"
                current = word

        if current:
            wrapped.append(current)
        return wrapped

    def render_fixed_info_panel(self, lines: list[str]) -> None:
        panel_rect = pygame.Rect(
            0, self.height - self.INFO_HEIGHT,
            self.width, self.INFO_HEIGHT
        )
        pygame.draw.rect(self.screen, (15, 15, 20), panel_rect)
        pygame.draw.line(
            self.screen, (40, 40, 60),
            (0, panel_rect.top), (self.width, panel_rect.top), 1
        )

        if not lines:
            lines = [""]
            accent_color = (0, 180, 205)
        else:
            header_type = lines[0].split(':')[0].upper()
            colors = {
                "DRONE": (255, 80, 80),
                "ZONE": (80, 255, 150),
                "LINK": (255, 200, 50)
            }
            accent_color = colors.get(header_type, (200, 200, 200))

        padding_x = 25
        max_content_width = self.width - (padding_x * 2) - 20

        pygame.draw.rect(
            self.screen, accent_color,
            (padding_x - 12, panel_rect.top + 15, 4, 80),
            border_radius=2
        )

        title_surf = self.text_font.render(lines[0], True, accent_color)
        self.screen.blit(title_surf, (padding_x, panel_rect.top + 12))

        curr_y = panel_rect.top + 12 + title_surf.get_height() + 2
        line_h = self.tooltip_font.get_height() + 2

        for ln in lines[1:]:
            for wrapped_line in self._wrap_text(ln, max_content_width):
                if curr_y + line_h > self.height - 8:
                    break
                surf = self.tooltip_font.render(
                    wrapped_line, True, (170, 175, 180)
                )
                self.screen.blit(surf, (padding_x, curr_y))
                curr_y += line_h

    def draw_ui(self) -> None:
        texto = f"Turn {self.turn_count}"
        text_surf = self.text_font.render(texto, True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(self.width // 2, self.HEIGHT // 2)
        )
        self.screen.blit(text_surf, text_rect)

    def setup_assets(self) -> None:
        raw_drone = pygame.image.load("imgs/drone.png").convert_alpha()
        d_size = (
            raw_drone.get_width() // 12,
            raw_drone.get_height() // 12
        )
        self.drone_img = pygame.transform.smoothscale(raw_drone, d_size)

        raw_zone = pygame.image.load("imgs/zone.png").convert_alpha()
        z_size = (
            raw_zone.get_width() // 15,
            raw_zone.get_height() // 15
        )
        self.zone_img = pygame.transform.smoothscale(raw_zone, z_size)

        self.zones_layer = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.draw_connections()
        self.draw_zones()
        self.create_drones()

    def create_drones(self) -> None:
        start, _ = self.d_map.zones["start"]

        sx = self._sx(start.x)
        sy = self._sy(start.y)

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

            p1 = (self._sx(z1.x), self._sy(z1.y))
            p2 = (self._sx(z2.x), self._sy(z2.y))

            pygame.draw.line(
                self.zones_layer, (35, 35, 35), p1, p2, width=6
            )
            pygame.draw.aaline(self.zones_layer, (80, 100, 120), p1, p2)

    def draw_zones(self) -> None:
        radius = self.scale // 3

        for (z, _) in self.d_map.zones.values():
            center = (self._sx(z.x), self._sy(z.y))
            draw_color = self.get_pygame_color(z.color)
            pygame.draw.circle(self.zones_layer, draw_color, center, radius)
            self.draw_img(self.zone_img, self.zones_layer, center)

    def draw_drones(self) -> None:
        for _, drone_data in self.d_map.drones.items():
            if drone_data[1] is not None:
                self.draw_img(
                    self.drone_img, self.screen, drone_data[1].center
                )
