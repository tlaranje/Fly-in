from pygame.typing import ColorLike
import pygame


class Button:
    win_size: tuple[int, int] = (0, 0)

    def __init__(
        self,
        pos: tuple[int | None, int | None],
        size: tuple[int, int],
        text: str,
        color: ColorLike = (100, 100, 100),
        hover_color: ColorLike = (150, 150, 150),
        border_color: ColorLike = (0, 0, 0),
        border_size: int = 1,
        border_radius: int = 20,
        action: str | None = None
    ) -> None:
        self.pos: tuple[int | None, int | None] = pos
        self.size: tuple[int, int] = size
        self.text: str = text
        self.color: ColorLike = color
        self.hover_color: ColorLike = hover_color
        self.action_value: str | None = action
        self.border_color: ColorLike = border_color
        self.border_size: int = border_size
        self.border_radius: int = border_radius
        self.rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.setup_button()

    def setup_button(self) -> None:
        x, y = self.pos
        size_x, size_y = self.size
        win_x, win_y = self.win_size
        pos_x = (win_x // 2) - (size_x // 2) if x is None else x
        pos_y = (win_y // 2) - (size_y // 2) if y is None else y
        self.rect = pygame.Rect(pos_x, pos_y, size_x, size_y)

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int]
    ) -> None:
        is_hover = self.rect.collidepoint(mouse_pos)
        current_color = self.hover_color if is_hover else self.color
        temp_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        pygame.draw.rect(
            temp_surface,
            current_color,
            (0, 0, self.rect.width, self.rect.height),
            border_radius=self.border_radius
        )

        if self.border_size > 0:
            pygame.draw.rect(
                temp_surface,
                self.border_color,
                (0, 0, self.rect.width, self.rect.height),
                self.border_size,
                border_radius=self.border_radius
            )

        txt_surf = font.render(self.text, True, (255, 255, 255))
        descent = font.get_descent()
        text_center = (
            self.rect.width // 2,
            (self.rect.height // 2) - (descent // 2)
        )
        txt_rect = txt_surf.get_rect(center=text_center)
        temp_surface.blit(txt_surf, txt_rect)
        screen.blit(temp_surface, self.rect.topleft)

    def is_clicked(
        self,
        mouse_pos: tuple[int, int],
        event: pygame.event.Event
    ) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False
