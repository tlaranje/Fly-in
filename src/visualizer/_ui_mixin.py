from typing import TYPE_CHECKING
import pygame

from ._protocol import VisualizerProtocol

if TYPE_CHECKING:
    from pygame import Surface


class UIMixin:
    """
    Turn counter, hover tooltip and fixed bottom info panel.

    Handles all dynamic UI elements redrawn every frame: the top bar
    turn counter, mouse-hover hit detection and the fixed info panel.
    """

    def draw_ui(self: VisualizerProtocol) -> None:
        """Draws the turn counter centred in the top bar."""
        texto: str = f"Turn {self.turn_count}"
        text_surf: "Surface" = self.text_font.render(
            texto, True, (255, 255, 255)
        )
        text_rect: pygame.Rect = text_surf.get_rect(
            center=(self.width // 2, self.TURN_HEIGHT // 2)
        )
        self.screen.blit(text_surf, text_rect)

    def draw_tooltip(self: VisualizerProtocol) -> None:
        """
        Detects the hovered element and updates the info panel.

        Priority order for hit detection:
        1. Drone sprites (rect collision).
        2. Zone circles (distance from centre).
        3. Connection lines (distance from segment).
        """
        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        m_vec: pygame.Vector2 = pygame.Vector2(mouse_pos)
        lines: list[str] = []

        # 1. Check drones
        for d_id, (d_obj, d_rect) in self.d_map.drones.items():
            if d_rect.collidepoint(mouse_pos):
                lines = [
                    f"DRONE {d_id}",
                    f"Drone id: {d_id}",
                    f"Current Zone: {d_obj.curr_zone}",
                ]
                break

        # 2. Check zones
        if not lines:
            radius: float = self.scale / 2.8
            for z_name, (z_obj, _) in self.d_map.zones.items():
                zsx: float = self.sx(z_obj.x)
                zsy: float = self.sy(z_obj.y)
                if m_vec.distance_to((zsx, zsy)) <= radius:
                    lines = [
                        f"ZONE: {z_name}",
                        f"Type: {z_obj.zone_type.name_str} | "
                        f"Max_drones: {z_obj.max_drones}",
                        f"Cost: {z_obj.zone_type.cost} | "
                        f"Priority: {z_obj.zone_type.priority}",
                    ]
                    break

        # 3. Check connections
        if not lines:
            for c_name, c_obj in self.d_map.connections.items():
                z1, _ = self.d_map.zones[c_obj.zone1]
                z2, _ = self.d_map.zones[c_obj.zone2]

                p1: pygame.Vector2 = pygame.Vector2(
                    self.sx(z1.x), self.sy(z1.y)
                )
                p2: pygame.Vector2 = pygame.Vector2(
                    self.sx(z2.x), self.sy(z2.y)
                )
                line_vec: pygame.Vector2 = p2 - p1

                if line_vec.length_squared() > 0:
                    # Project mouse onto segment, clamp to [0, 1]
                    t: float = (
                        (m_vec - p1).dot(line_vec)
                        / line_vec.length_squared()
                    )
                    t = max(0.0, min(1.0, t))
                    if m_vec.distance_to(p1 + t * line_vec) < 8:
                        lines = [
                            f"LINK: {c_name}",
                            f"From: {c_obj.zone1} | To: {c_obj.zone2}",
                            f"Capacity: {c_obj.max_link_capacity}",
                        ]
                        break

        self.render_fixed_info_panel(lines)

    def render_fixed_info_panel(
        self: VisualizerProtocol, lines: list[str]
    ) -> None:
        """
        Draws the fixed bottom info panel split into two columns.

        The left column shows hovered element details; the right column
        shows a static keybinds reference.  Accent bar and title colour
        are derived from the element type keyword (DRONE / ZONE / LINK).

        Args:
            lines: First element is the panel title; remaining elements
                are detail rows. Pass an empty list for the idle state.
        """
        panel_rect: pygame.Rect = pygame.Rect(
            0, self.height - self.INFO_HEIGHT,
            self.width, self.INFO_HEIGHT,
        )

        # Panel background and top border.
        pygame.draw.rect(self.screen, (15, 15, 20), panel_rect)
        pygame.draw.line(
            self.screen, (40, 40, 60),
            (0, panel_rect.top), (self.width, panel_rect.top), 1,
        )

        # Resolve accent colour from the element type keyword.
        if not lines:
            lines = [""]
            accent_color: tuple[int, int, int] = (0, 180, 205)
        else:
            header_type: str = lines[0].split(":")[0].upper()
            color_map: dict[str, tuple[int, int, int]] = {
                "DRONE": (255, 80, 80),
                "ZONE": (80, 255, 150),
                "LINK": (255, 200, 50),
            }
            accent_color = color_map.get(header_type, (200, 200, 200))

        # --- Left column: hovered element info ---
        left_x: int = 25
        col_divider: int = self.width // 2

        # Coloured left accent bar.
        pygame.draw.rect(
            self.screen, accent_color,
            (left_x - 12, panel_rect.top + 15, 4, 80),
            border_radius=2,
        )

        # Title row.
        title_surf: "Surface" = self.text_font.render(
            lines[0], True, accent_color
        )
        self.screen.blit(title_surf, (left_x, panel_rect.top + 12))

        curr_y: int = panel_rect.top + 12 + title_surf.get_height() + 2
        line_h: int = self.tooltip_font.get_height() + 2

        # Detail rows — clipped to the panel bottom and column boundary.
        for ln in lines[1:]:
            if curr_y + line_h > self.height - 8:
                break
            surf: "Surface" = self.tooltip_font.render(
                ln, True, (170, 175, 180)
            )
            # Clip to left column width.
            if surf.get_width() > col_divider - left_x - 8:
                surf = surf.subsurface(
                    (0, 0, col_divider - left_x - 8, surf.get_height())
                )
            self.screen.blit(surf, (left_x, curr_y))
            curr_y += line_h

        # --- Vertical divider between columns ---
        pygame.draw.line(
            self.screen, (40, 40, 60),
            (col_divider, panel_rect.top + 10),
            (col_divider, self.height - 10), 1,
        )

        # --- Right column: static keybinds reference ---
        keybinds: list[tuple[str, str]] = [
            ("RIGT ARROW", "Next turn"),
            ("M", "Toggle auto / manual"),
            ("R", "Reset simulation"),
            ("ESC", "Quit"),
        ]

        right_x: int = col_divider + 20
        kb_color: tuple[int, int, int] = (0, 180, 205)

        # Keybinds column header.
        header_surf: "Surface" = self.text_font.render(
            "KEYBINDS", True, kb_color
        )
        self.screen.blit(header_surf, (right_x, panel_rect.top + 12))

        # Coloured accent bar for the right column.
        pygame.draw.rect(
            self.screen, kb_color,
            (right_x - 12, panel_rect.top + 15, 4, 80),
            border_radius=2,
        )

        kb_y: int = panel_rect.top + 12 + header_surf.get_height() + 2

        for key, description in keybinds:
            if kb_y + line_h > self.height - 8:
                break

            # Key badge — rendered in accent colour.
            key_surf: "Surface" = self.tooltip_font.render(
                f"[{key}]", True, (0, 180, 205)
            )
            self.screen.blit(key_surf, (right_x, kb_y))

            # Description — rendered in muted grey.
            desc_surf: "Surface" = self.tooltip_font.render(
                description, True, (170, 175, 180)
            )
            self.screen.blit(
                desc_surf,
                (right_x + key_surf.get_width() + 8, kb_y),
            )
            kb_y += line_h
