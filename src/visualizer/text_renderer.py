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
        center_pos: tuple[int, int],
        thickness: int = 1
    ) -> None:
        # Renderiza a base do texto
        text_surf = font.render(text, True, color)

        # Cria as posições do contorno
        x, y = center_pos
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx == 0 and dy == 0:
                    continue
                outline_surf = font.render(text, True, outline_color)
                outline_rect = outline_surf.get_rect(center=(x + dx, y + dy))
                screen.blit(outline_surf, outline_rect)

        # Renderiza o texto principal no centro exato
        text_rect = text_surf.get_rect(center=center_pos)
        screen.blit(text_surf, text_rect)
