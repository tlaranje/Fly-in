from typing import TYPE_CHECKING
import pygame

from ._window_mixin import WindowMixin
from ._renderer_mixin import RendererMixin
from ._ui_mixin import UIMixin

if TYPE_CHECKING:
    from src.core import DroneMap
    from pygame import Surface


class Visualizer(
    WindowMixin,
    RendererMixin,
    UIMixin,
):
    """
    pygame renderer for the drone simulation.

    Inherits coordinate helpers from VisualizerWindowMixin, static and
    dynamic drawing from VisualizerRendererMixin, and all UI / tooltip
    logic from VisualizerUIMixin.

    Only ``__init__`` lives here — it declares every attribute shared
    across the three mixins so the full interface is visible in one place.

    Attributes:
        MIN_WIDTH: Minimum window width (declared in VisualizerWindowMixin).
        d_map: The drone map being visualised.
        scale: Pixels per world unit.
        margin: Pixel padding around the map content.
        width: Current window width in pixels.
        height: Current window height in pixels.
        offset_x: Minimum world X used to shift coordinates to origin.
        offset_y: Minimum world Y used to shift coordinates to origin.
        center_offset_x: Extra shift to horizontally centre the map.
        turn_count: Number of turns elapsed.
        TURN_HEIGHT: Height of the top turn-counter bar in pixels.
        INFO_HEIGHT: Height of the bottom info panel in pixels.
        screen: The active pygame display surface.
        drone_img: Scaled drone sprite surface.
        zone_img: Scaled zone icon surface.
        zones_layer: Pre-rendered static layer (zones + connections).
        text_font: Bold font used for titles and the turn counter.
        tooltip_font: Regular font used for panel detail lines.
    """

    def __init__(self, d_map: "DroneMap") -> None:
        """
        Initializes all shared attributes used by the mixin methods.

        Args:
            d_map: The parsed drone map to render.
        """
        pygame.init()

        self.d_map: "DroneMap" = d_map
        self.scale: int = 80
        self.margin: int = 64

        self.width: int = 0
        self.height: int = 0

        # Assigned in setup_assets()
        self.drone_img: "Surface"
        self.zone_img: "Surface"
        self.zones_layer: "Surface"

        # Assigned in setup_window()
        self.screen: "Surface"

        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.center_offset_x: int = 0
        self.turn_count: int = 0

        self.text_font: pygame.font.Font = pygame.font.SysFont(
            "Arial", 30, bold=True
        )
        self.tooltip_font: pygame.font.Font = pygame.font.SysFont(
            "Arial", 20, bold=False
        )

        # Layout constants used by both window and UI mixins
        self.TURN_HEIGHT: int = 60
        self.INFO_HEIGHT: int = 155

        self.drone_frames: list["Surface"] = []
        self.drone_frame_index: int = 0
        self.drone_frame_timer: int = 0
        self.drone_frame_interval: int = 2
