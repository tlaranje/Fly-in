from .text_renderer import TextRenderer
from pygame.typing import ColorLike
import pygame


class Button:
    win_size: tuple[int, int] = (0, 0)

    def __init__(
        self,
        pos: tuple[int | None, int | None],
        size: tuple[int, int],
        text: str,
        color: ColorLike = (50, 50, 50),
        hover_color: ColorLike = (70, 90, 230),
        action: str | None = None
    ) -> None:
        self.pos = pos
        self.size = size
        self.text = text
        self.base_color = pygame.Color(color)
        self.hover_color = pygame.Color(hover_color)
        self.action_value = action
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.setup_button()

    def setup_button(self) -> None:
        x, y = self.pos
        win_x, win_y = self.win_size
        pos_x = (win_x // 2) - (self.size[0] // 2) if x is None else x
        pos_y = (win_y // 2) - (self.size[1] // 2) if y is None else y
        self.rect.topleft = (pos_x, pos_y)

    def draw_gradient(self, surface, color, rect, radius):
        fill_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        for i in range(rect.height):
            factor = 1.0 - (i / rect.height) * 0.15
            c = (
                int(color.r * factor),
                int(color.g * factor),
                int(color.b * factor)
            )
            pygame.draw.line(fill_surf, c, (0, i), (rect.width, i))

        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            mask, (255, 255, 255), (0, 0, *rect.size), border_radius=radius
        )
        fill_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(fill_surf, rect.topleft)

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int]
    ) -> None:
        is_hover = self.rect.collidepoint(mouse_pos)
        is_pressed = is_hover and pygame.mouse.get_pressed()[0]

        target_color = self.hover_color if is_hover else self.base_color
        offset = 2 if is_pressed else 0

        if is_hover:
            glow_rect = self.rect
            glow_color = (*target_color[:3], 60)
            pygame.draw.rect(screen, glow_color, glow_rect, border_radius=14)

        draw_rect = self.rect.move(0, offset)
        self.draw_gradient(screen, target_color, draw_rect, 12)

        border_color = (200, 200, 200) if not is_hover else (255, 255, 255)
        pygame.draw.rect(screen, border_color, draw_rect, 2, border_radius=12)

        TextRenderer.draw_with_outline(
            screen,
            self.text,
            font,
            (255, 255, 255),
            (0, 0, 0),
            draw_rect.center,
            thickness=1
        )

    def is_clicked(
        self, mouse_pos: tuple[int, int], event: pygame.event.Event
    ) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False
