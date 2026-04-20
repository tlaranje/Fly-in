from typing import TYPE_CHECKING
import pygame

from ._protocol import VisualizerProtocol

if TYPE_CHECKING:
    from pygame import Surface


class RendererMixin:
    """
    Asset loading and static/dynamic element rendering.

    Responsible for loading images, pre-rendering the static map layer
    (zones + connections) and drawing drone sprites each frame.
    """

    def setup_assets(self: VisualizerProtocol) -> None:
        """
        Loads and scales images, then pre-renders the static map layer.

        The static layer is drawn once onto ``zones_layer`` and blitted
        each frame, avoiding redundant calls for elements that never
        change at runtime.
        """
        raw_drone: "Surface" = pygame.image.load(
            "imgs/drone_f0.png"
        ).convert_alpha()
        d_size: tuple[int, int] = (
            raw_drone.get_width() // 12,
            raw_drone.get_height() // 12,
        )

        self.drone_frames = []
        for i in range(16):
            raw = pygame.image.load(f"imgs/drone_f{i}.png").convert_alpha()
            d_size = (raw.get_width() // 5, raw.get_height() // 5)
            self.drone_frames.append(pygame.transform.smoothscale(raw, d_size))

        self.drone_img = self.drone_frames[0]

        raw_zone: "Surface" = pygame.image.load(
            "imgs/zone.png"
        ).convert_alpha()
        z_size: tuple[int, int] = (
            raw_zone.get_width() // 15,
            raw_zone.get_height() // 15,
        )
        self.zone_img = pygame.transform.smoothscale(raw_zone, z_size)

        # Transparent surface used as the static background layer
        self.zones_layer = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.draw_connections()
        self.draw_zones()
        self.create_drones()

    def create_drones(self: VisualizerProtocol) -> None:
        """
        Spawns all drone sprites at the start zone screen position.

        Resets world-space target coordinates and creates a pygame Rect
        for each drone centred on the start zone.
        """
        start, _ = self.d_map.zones["start"]

        spawn_x: float = self.sx(start.x)
        spawn_y: float = self.sy(start.y)

        for d_id, d_data in self.d_map.drones.items():
            d_obj = d_data[0]
            d_obj.curr_zone = "start"
            d_obj.target_x = float(start.x)
            d_obj.target_y = float(start.y)
            rect: pygame.Rect = self.drone_img.get_rect(
                center=(spawn_x, spawn_y)
            )
            self.d_map.drones[d_id] = (d_obj, rect)

    def get_pygame_color(
        self: VisualizerProtocol, color_str: str | None
    ) -> pygame.Color:
        """
        Resolves a color string to a pygame.Color with special aliases.

        Args:
            color_str: A pygame color name, a hard-coded alias, or None.

        Returns:
            A valid pygame.Color. Falls back to gray on unknown values.
        """
        if color_str is None:
            return pygame.Color("gray")

        # Extra aliases not natively supported by pygame
        specials: dict[str, tuple[int, int, int]] = {
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
        self: VisualizerProtocol,
        img: "Surface",
        layer: "Surface",
        center: tuple[float, float],
    ) -> None:
        """
        Blits *img* centred on *center* onto *layer*.

        Args:
            img: Surface to blit.
            layer: Destination surface.
            center: (x, y) screen position for the image centre.
        """
        imagerect: pygame.Rect = img.get_rect(center=center)
        layer.blit(img, imagerect)

    def draw_connections(self: VisualizerProtocol) -> None:
        """
        Draws all connection lines onto the static zones layer.

        Each link is drawn twice: a thick dark line for the body and a
        thin anti-aliased line on top for a subtle highlight effect.
        """
        for _, c_obj in self.d_map.connections.items():
            z1, _ = self.d_map.zones[c_obj.zone1]
            z2, _ = self.d_map.zones[c_obj.zone2]

            p1: tuple[float, float] = (self.sx(z1.x), self.sy(z1.y))
            p2: tuple[float, float] = (self.sx(z2.x), self.sy(z2.y))

            # Body — thick dark line
            pygame.draw.line(
                self.zones_layer, (35, 35, 35), p1, p2, width=6
            )
            # Highlight — thin anti-aliased overlay
            pygame.draw.aaline(self.zones_layer, (80, 100, 120), p1, p2)

    def draw_zones(self: VisualizerProtocol) -> None:
        """Draws all zone circles and icons onto the static zones layer."""
        radius: int = self.scale // 3

        for z, _ in self.d_map.zones.values():
            center: tuple[float, float] = (self.sx(z.x), self.sy(z.y))
            draw_color: pygame.Color = self.get_pygame_color(z.color)
            pygame.draw.circle(
                self.zones_layer, draw_color, center, radius
            )
            self.draw_img(self.zone_img, self.zones_layer, center)

    def draw_drones(self: VisualizerProtocol) -> None:
        """Draws all active drone sprites onto the main screen surface."""
        current_frame = self.drone_frames[self.drone_frame_index]
        for _, drone_data in self.d_map.drones.items():
            _, d_rect = drone_data
            if d_rect is not None:
                x, y = d_rect.center
                center = (x, y - 4)
                self.draw_img(current_frame, self.screen, center)
