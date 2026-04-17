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

    def draw_tooltip(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        m_vec = pygame.Vector2(mouse_pos)
        lines = []

        # 1. Drones
        for d_id, (d_obj, d_rect) in self.d_map.drones.items():
            if d_rect.collidepoint(mouse_pos):
                lines = [
                    f"Drone {d_id}",
                    f"Id: {d_id}",
                    f"Zone: {d_obj.curr_zone}"
                ]
                break

        # 2. Zonas
        if not lines:
            radius = self.scale // 2.8
            for z_name, (z_obj, _) in self.d_map.zones.items():
                sx = (z_obj.x - self.offset_x) * self.scale + self.margin
                sy = (z_obj.y - self.offset_y) * self.scale + self.margin
                center = pygame.Vector2(sx, sy)

                if m_vec.distance_to(center) <= radius:
                    lines = [
                        f"{z_name}",
                        f"X: {z_obj.x}, Y: {z_obj.y}",
                        f"Type: {z_obj.zone_type.name_str}",
                        f"Cost: {z_obj.zone_type.cost}",
                        f"Priority: {z_obj.zone_type.priority}",
                        f"Color: {z_obj.color}",
                        f"Max_drones: {z_obj.max_drones}",
                        f"Count_drones: {z_obj.count_drones}"
                    ]
                    break

        # 3. Links (Conexões)
        if not lines:
            for c_name, c_obj in self.d_map.connections.items():
                z1 = self.d_map.zones[c_obj.zone1][0]
                z2 = self.d_map.zones[c_obj.zone2][0]
                p1 = pygame.Vector2(
                    (z1.x - self.offset_x) * self.scale + self.margin,
                    (z1.y - self.offset_y) * self.scale + self.margin
                )
                p2 = pygame.Vector2(
                    (z2.x - self.offset_x) * self.scale + self.margin,
                    (z2.y - self.offset_y) * self.scale + self.margin
                )

                line_vec = p2 - p1
                if line_vec.length_squared() > 0:
                    t = (m_vec - p1).dot(line_vec) / line_vec.length_squared()
                    t = max(0, min(1, t))
                    proj = p1 + t * line_vec
                    if m_vec.distance_to(proj) < 8:
                        lines = [
                            f"{c_name}",
                            f"From: {c_obj.zone1}",
                            f"To: {c_obj.zone2}",
                            f"Max_link_capacit: {c_obj.max_link_capacity}",
                        ]
                        break

        if lines:
            self.render_tooltip_box(lines, mouse_pos)

    def render_tooltip_box(self, lines: list[str], pos: tuple) -> None:
        padding = 10
        line_spacing = 4
        border_color = (100, 100, 120)
        bg_color = (25, 25, 30, 240)

        rendered = [
            self.tooltip_font.render(ln, True, (255, 255, 255)) for ln in lines
        ]

        title_h = rendered[0].get_height()
        w = max(s.get_width() for s in rendered) + (padding * 2)
        h = sum(s.get_height() for s in rendered) + (padding * 2)
        h += (line_spacing * len(lines)) + 8

        off_x, off_y = pos[0] + 20, pos[1] + 20

        if off_x + w > self.width:
            off_x = pos[0] - w - 20

        if off_y + h > self.height:
            off_y = pos[1] - h - 20

        off_x = max(0, off_x)
        off_y = max(0, off_y)

        rect = pygame.Rect(off_x, off_y, w, h)

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            overlay, bg_color, (0, 0, w, h), border_radius=10
        )
        pygame.draw.rect(
            overlay, border_color, (0, 0, w, h), 2, border_radius=10
        )
        self.screen.blit(overlay, rect)

        t_surf = rendered[0]
        t_x = rect.x + (w - t_surf.get_width()) // 2
        self.screen.blit(t_surf, (t_x, rect.y + padding))

        line_y = rect.y + padding + title_h + (line_spacing // 2) + 2
        pygame.draw.line(
            self.screen, border_color, (rect.x + 2, line_y),
            (rect.x + w - 2, line_y), 2
        )

        curr_y = line_y + line_spacing + 5
        for s in rendered[1:]:
            self.screen.blit(s, (rect.x + padding, curr_y))
            curr_y += s.get_height() + line_spacing

    def draw_ui(self) -> None:
        texto = f"Turn {self.turn_count}"
        text_surface = self.text_font.render(texto, True, (255, 255, 255))

        text_rect = text_surface.get_rect(center=(self.width // 2, 30))

        self.screen.blit(text_surface, text_rect)

    def setup_assets(self) -> None:
        raw_drone = pygame.image.load("imgs/drone.png").convert_alpha()
        drone_size = (
            raw_drone.get_width() // 12, raw_drone.get_height() // 12
        )
        self.drone_img = pygame.transform.smoothscale(raw_drone, drone_size)

        raw_zone = pygame.image.load("imgs/zone.png").convert_alpha()
        zone_size = (raw_zone.get_width() // 15, raw_zone.get_height() // 15)
        self.zone_img = pygame.transform.smoothscale(raw_zone, zone_size)

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
            drone_obj.curr_zone = "start"
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
        self, img: "Surface", layer: "Surface", center: tuple
    ) -> None:
        imagerect = img.get_rect()
        imagerect.center = center
        layer.blit(img, imagerect)

    def draw_connections(self):
        for conn_name, conn_obj in self.d_map.connections.items():
            z1 = self.d_map.zones[conn_obj.zone1][0]
            z2 = self.d_map.zones[conn_obj.zone2][0]

            s_pos = (
                (z1.x - self.offset_x) * self.scale + self.margin,
                (z1.y - self.offset_y) * self.scale + self.margin
            )
            e_pos = (
                (z2.x - self.offset_x) * self.scale + self.margin,
                (z2.y - self.offset_y) * self.scale + self.margin
            )

            pygame.draw.line(
                self.zones_layer, (35, 35, 35), s_pos, e_pos, width=6
            )

            main_color = (80, 100, 120)
            pygame.draw.aaline(
                self.zones_layer, main_color, s_pos, e_pos, width=4
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
            self.draw_img(self.zone_img, self.zones_layer, center)

    def draw_drones(self) -> None:
        for _, drone_data in self.d_map.drones.items():
            assert drone_data[1] is not None
            self.draw_img(self.drone_img, self.screen, drone_data[1].center)
