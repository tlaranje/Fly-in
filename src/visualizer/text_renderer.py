from pygame.typing import ColorLike
import pygame


class TextRenderer:
    """
    Utility class for rendering outlined text onto pygame surfaces.

    All methods are static — this class is a namespace, not meant to
    be instantiated.
    """

    @staticmethod
    def draw_with_outline(
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: ColorLike,
        outline_color: ColorLike,
        center_pos: tuple[int, int],
        thickness: int = 1,
    ) -> None:
        """
        Draws *text* centred on *center_pos* with a solid outline.

        Renders the outline by blitting the text multiple times in
        *outline_color* at every (dx, dy) offset within *thickness*,
        then blits the main text on top in *color*.

        Args:
            screen: Destination surface to draw on.
            text: The string to render.
            font: pygame font used for rendering.
            color: Fill colour of the main text.
            outline_color: Colour of the outline strokes.
            center_pos: (x, y) screen position for the text centre.
            thickness: Outline width in pixels. Defaults to 1.
        """
        # Render the main text surface once and reuse it
        text_surf: pygame.Surface = font.render(text, True, color)

        x, y = center_pos

        # Draw the outline by rendering at every offset around (0, 0)
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx == 0 and dy == 0:
                    # Skip centre — that position is for the main text
                    continue
                outline_surf: pygame.Surface = font.render(
                    text, True, outline_color
                )
                outline_rect: pygame.Rect = outline_surf.get_rect(
                    center=(x + dx, y + dy)
                )
                screen.blit(outline_surf, outline_rect)

        # Blit the main text on top, perfectly centred
        text_rect: pygame.Rect = text_surf.get_rect(center=center_pos)
        screen.blit(text_surf, text_rect)
