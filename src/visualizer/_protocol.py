# _protocols.py

from typing import TYPE_CHECKING, Protocol
import pygame

if TYPE_CHECKING:
    from src.core import DroneMap
    from pygame import Surface


class VisualizerProtocol(Protocol):
    """Declares every attribute and method the mixins expect."""

    # --- Map data ---
    d_map: "DroneMap"

    # --- Rendering constants ---
    scale: int
    margin: int
    TURN_HEIGHT: int
    INFO_HEIGHT: int

    # --- Computed window geometry ---
    width: int
    height: int
    offset_x: float
    offset_y: float
    center_offset_x: int

    # --- pygame objects ---
    screen: "Surface"
    drone_img: "Surface"
    zone_img: "Surface"
    zones_layer: "Surface"

    # --- Fonts ---
    text_font: pygame.font.Font
    tooltip_font: pygame.font.Font

    # --- State ---
    turn_count: int

    # --- Window mixin ---
    def setup_window(self) -> None: ...
    def sx(self, world_x: float) -> float: ...
    def sy(self, world_y: float) -> float: ...

    # --- Renderer mixin ---
    def draw_connections(self) -> None: ...
    def draw_zones(self) -> None: ...
    def create_drones(self) -> None: ...
    def setup_assets(self) -> None: ...
    def get_pygame_color(self, color_str: str | None) -> pygame.Color: ...
    def draw_drones(self) -> None: ...

    def draw_img(
            self,
            img: "Surface",
            layer: "Surface",
            center: tuple[float, float],
    ) -> None: ...

    # --- UI mixin ---
    def render_fixed_info_panel(self, lines: list[str]) -> None: ...
    def draw_ui(self) -> None: ...
    def draw_tooltip(self) -> None: ...
