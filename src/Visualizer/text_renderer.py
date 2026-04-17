from pygame.typing import ColorLike
import pygame


class TextRenderer:
    @staticmethod
    def draw_with_outline(
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: ColorLike,
        outline_color: ColorLike,
        pos: tuple[float, float],
        thickness: int = 2
    ) -> None:
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=pos)

        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    screen.blit(
                        outline_surf,
                        (text_rect.x + dx, text_rect.y + dy)
                    )

        screen.blit(text_surf, text_rect)
