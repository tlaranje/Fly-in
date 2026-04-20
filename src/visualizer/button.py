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
        color: ColorLike = (20, 100, 155),
        hover_color: ColorLike = (30, 160, 160),
        border_color: ColorLike = (255, 255, 255),
        border_size: int = 3,
        round_size: int = 25,
        action: str | None = None,
    ) -> None:
        self.pos: tuple[int | None, int | None] = pos
        self.size: tuple[int, int] = size
        self.text: str = text
        self.base_color: pygame.Color = pygame.Color(color)
        self.hover_color: pygame.Color = pygame.Color(hover_color)
        self.border_color: pygame.Color = pygame.Color(border_color)
        self.border_size: int = border_size
        self.round_size: int = round_size
        self.action_value: str | None = action
        self.rect: pygame.Rect = pygame.Rect(0, 0, size[0], size[1])
        self.setup_button()

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

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int],
    ) -> None:
        is_hover: bool = self.rect.collidepoint(mouse_pos)
        is_pressed: bool = is_hover and pygame.mouse.get_pressed()[0]

        target_color: pygame.Color = (
            self.hover_color if is_hover else self.base_color
        )
        offset: int = 2 if is_pressed else 0
        draw_rect: pygame.Rect = self.rect.move(0, offset)

        # Sombra deslocada (só aparece quando não está pressionado)
        if not is_pressed:
            shadow_rect: pygame.Rect = draw_rect.move(3, 4)
            pygame.draw.rect(
                screen, (20, 20, 20), shadow_rect,
                border_radius=self.round_size
            )

        # Glow no hover
        if is_hover:
            glow_color: tuple[int, ...] = (*target_color[:3], 60)
            pygame.draw.rect(
                screen, glow_color, self.rect,
                border_radius=self.round_size + 2
            )

        # Botão principal
        pygame.draw.rect(
            screen, target_color, draw_rect,
            border_radius=self.round_size
        )

        # Borda
        pygame.draw.rect(
            screen, self.border_color, draw_rect,
            self.border_size,
            border_radius=self.round_size
        )

        x, y = draw_rect.center
        TextRenderer.draw_with_outline(
            screen,
            self.text,
            font,
            (255, 255, 255),
            (0, 0, 0),
            (x, y + 3),
            thickness=1,
        )

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
