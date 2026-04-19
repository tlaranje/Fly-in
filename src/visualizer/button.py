from .text_renderer import TextRenderer
from pygame.typing import ColorLike
import pygame


class Button:
    """
    A styled pygame button with gradient fill, glow and outline text.

    Supports hover and press states, optional centring via ``None``
    coordinates, and a string action value used by the caller to
    identify which button was clicked.

    Attributes:
        win_size: Shared window size used to centre buttons when a
            position axis is None. Must be updated whenever the window
            is resized before calling ``setup_button()``.
        pos: Requested (x, y) position. None on either axis means
            "centre on that axis within win_size".
        size: Button dimensions as (width, height) in pixels.
        text: Label rendered on the button face.
        base_color: Fill colour when idle.
        hover_color: Fill colour when the mouse is over the button.
        action_value: Arbitrary string the caller reads on click.
        rect: The computed bounding rectangle, updated by setup_button().
    """

    win_size: tuple[int, int] = (0, 0)

    def __init__(
        self,
        pos: tuple[int | None, int | None],
        size: tuple[int, int],
        text: str,
        color: ColorLike = (50, 50, 50),
        hover_color: ColorLike = (70, 90, 230),
        action: str | None = None,
    ) -> None:
        """
        Creates a button and computes its initial screen position.

        Args:
            pos: (x, y) screen position. Pass None on either axis to
                centre the button on that axis using win_size.
            size: Button (width, height) in pixels.
            text: Label to display on the button.
            color: Idle background colour. Defaults to dark grey.
            hover_color: Background colour on mouse hover.
            action: String identifier returned to the caller on click.
        """
        self.pos: tuple[int | None, int | None] = pos
        self.size: tuple[int, int] = size
        self.text: str = text
        self.base_color: pygame.Color = pygame.Color(color)
        self.hover_color: pygame.Color = pygame.Color(hover_color)
        self.action_value: str | None = action
        self.rect: pygame.Rect = pygame.Rect(0, 0, size[0], size[1])
        self.setup_button()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def setup_button(self) -> None:
        """
        Recomputes rect.topleft from pos and the current win_size.

        Call this after every window resize so buttons that use None
        axes are re-centred correctly.
        """
        x, y = self.pos
        win_x, win_y = self.win_size

        # None means "centre on this axis"
        pos_x: int = (win_x // 2) - (self.size[0] // 2) if x is None else x
        pos_y: int = (win_y // 2) - (self.size[1] // 2) if y is None else y
        self.rect.topleft = (pos_x, pos_y)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_gradient(
        self,
        surface: pygame.Surface,
        color: pygame.Color,
        rect: pygame.Rect,
        radius: int,
    ) -> None:
        """
        Draws a gradient fill clipped to a rounded rectangle.

        Creates a temporary SRCALPHA surface, fills it row-by-row with a
        slightly darker shade towards the bottom, then masks it with a
        rounded rectangle before blitting onto *surface*.

        Args:
            surface: Destination surface.
            color: Base colour for the top of the gradient.
            rect: Area and position to fill.
            radius: Corner radius for the rounded rectangle mask.
        """
        fill_surf: pygame.Surface = pygame.Surface(rect.size, pygame.SRCALPHA)

        for i in range(rect.height):
            # Darken by up to 15 % towards the bottom
            factor: float = 1.0 - (i / rect.height) * 0.15
            row_color: tuple[int, int, int] = (
                int(color.r * factor),
                int(color.g * factor),
                int(color.b * factor),
            )
            pygame.draw.line(fill_surf, row_color, (0, i), (rect.width, i))

        # Clip gradient to the rounded-rect shape using a white alpha mask
        mask: pygame.Surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            mask, (255, 255, 255), (0, 0, *rect.size), border_radius=radius
        )
        fill_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(fill_surf, rect.topleft)

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int],
    ) -> None:
        """
        Renders the button in its current hover/press state.

        Draw order:
        1. Glow halo (hover only).
        2. Gradient fill.
        3. Rounded border.
        4. Outlined label text.

        Args:
            screen: Surface to draw onto.
            font: Font used for the button label.
            mouse_pos: Current mouse position for hover/press detection.
        """
        is_hover: bool = self.rect.collidepoint(mouse_pos)
        is_pressed: bool = is_hover and pygame.mouse.get_pressed()[0]

        target_color: pygame.Color = (
            self.hover_color if is_hover else self.base_color
        )
        # Shift the button down slightly when pressed for tactile feel
        offset: int = 2 if is_pressed else 0

        if is_hover:
            # Soft glow halo behind the button
            glow_color: tuple[int, ...] = (*target_color[:3], 60)
            pygame.draw.rect(
                screen, glow_color, self.rect, border_radius=14
            )

        draw_rect: pygame.Rect = self.rect.move(0, offset)
        self.draw_gradient(screen, target_color, draw_rect, 12)

        border_color: tuple[int, int, int] = (
            (255, 255, 255) if is_hover else (200, 200, 200)
        )
        pygame.draw.rect(
            screen, border_color, draw_rect, 2, border_radius=12
        )

        TextRenderer.draw_with_outline(
            screen,
            self.text,
            font,
            (255, 255, 255),
            (0, 0, 0),
            draw_rect.center,
            thickness=1,
        )

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def is_clicked(
        self,
        mouse_pos: tuple[int, int],
        event: pygame.event.Event,
    ) -> bool:
        """
        Returns True if this button was left-clicked in *event*.

        Args:
            mouse_pos: Current mouse position.
            event: The pygame event to inspect.

        Returns:
            True when the event is a left mouse button down inside the
            button rect, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False
