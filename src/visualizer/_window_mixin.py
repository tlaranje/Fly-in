import pygame

from ._protocol import VisualizerProtocol


class WindowMixin:
    """
    Window creation and world-to-screen coordinate conversion.

    Attributes:
        MIN_WIDTH: Minimum window width so the info panel always fits.
    """

    MIN_WIDTH: int = 1013

    def setup_window(self: VisualizerProtocol) -> None:
        """
        Computes window dimensions from map extents and opens it.

        Enforces MIN_WIDTH so the info panel is never too narrow, and
        computes center_offset_x so small maps appear centred.
        """
        all_x: list[int] = [z.x for z, _ in self.d_map.zones.values()]
        all_y: list[int] = [z.y for z, _ in self.d_map.zones.values()]

        self.offset_x = float(min(all_x))
        self.offset_y = float(min(all_y))
        max_x, max_y = max(all_x), max(all_y)

        # Natural width the map content would require
        map_width: int = int(
            (max_x - self.offset_x) * self.scale + self.margin * 2
        )
        self.width = max(WindowMixin.MIN_WIDTH, map_width)

        # Shift map right so it is centred inside a wider window
        self.center_offset_x = (self.width - map_width) // 2

        self.height = (
            int((max_y - self.offset_y) * self.scale + self.margin * 2)
            + self.TURN_HEIGHT + self.INFO_HEIGHT
        )

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fly-in")

    def sx(self: VisualizerProtocol, world_x: float) -> float:
        """
        Converts a world X coordinate to a screen X pixel.

        Args:
            world_x: X position in world space.

        Returns:
            Corresponding screen X position in pixels.
        """
        return (
            (world_x - self.offset_x) * self.scale
            + self.margin + self.center_offset_x
        )

    def sy(self: VisualizerProtocol, world_y: float) -> float:
        """
        Converts a world Y coordinate to a screen Y pixel.

        Args:
            world_y: Y position in world space.

        Returns:
            Corresponding screen Y position, offset by the top bar.
        """
        return (
            (world_y - self.offset_y) * self.scale
            + self.margin + self.TURN_HEIGHT
        )
