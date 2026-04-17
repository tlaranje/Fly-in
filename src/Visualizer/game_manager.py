from .text_renderer import TextRenderer
from .button import Button
import pygame
import sys
import os


class GameManager:
    def __init__(self) -> None:
        pygame.init()
        self.win_size: tuple[int, int] = (250, 260)
        Button.win_size = self.win_size
        self.btm_size: tuple[int, int] = (200, 60)
        self.center_window()
        self.screen: pygame.Surface = pygame.display.set_mode(self.win_size)
        pygame.display.set_caption("Fly-in")

        self.title_font: pygame.font.Font = pygame.font.SysFont(
            'arialblack', 80, bold=True
        )
        self.font: pygame.font.Font = pygame.font.SysFont('arial', 35)
        self.small_font: pygame.font.Font = pygame.font.SysFont('arial', 25)

        self.state: str = 'MAIN_MENU'
        self.selected_difficulty: str | None = None
        self.menu_buttons: list[Button] = [
            Button(
                (None, 100), self.btm_size, "Play", action="START_MAP_SELECT"
            ),
            Button(
                (None, 180), self.btm_size, "Exit", action="QUIT_APP"
            )
        ]

        self.difficulty_btms: list[Button] = []
        difficulties = [
            ("Easy", "EASY_MODE"),
            ("Medium", "MEDIUM_MODE"),
            ("Hard", "HARD_MODE"),
            ("Challenger", "CHALLENGER_MODE"),
        ]

        for i, (nome, acao) in enumerate(difficulties):
            y_pos = 80 + (i * 80)
            self.difficulty_btms.append(
                Button((None, y_pos), self.btm_size, nome, action=acao)
            )

        self.maps_data: dict[str, list[str]] = {
            "EASY_MODE": ["Linear Path", "Simple Fork", "Basic Capacity"],
            "MEDIUM_MODE": [
                "Dead End Trap", "Circular Loop", "Priority Puzzle"
            ],
            "HARD_MODE": [
                "Maze Nightmare", "Capacity Hell", "Ultimate Challenge"
            ],
            "CHALLENGER_MODE": ["Impossible Dream"]
        }
        self.active_map_buttons: list[Button] = []

    def center_window(self) -> None:
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def create_map_screen(self) -> None:
        self.active_map_buttons = []
        maps = self.maps_data.get(self.selected_difficulty or "", [])
        new_height = 120 + (len(maps) * 70)
        self.win_size = (400, max(300, new_height))
        Button.win_size = self.win_size
        self.screen = pygame.display.set_mode(self.win_size)

        for i, map_name in enumerate(maps):
            y_pos = 100 + (i * 70)
            self.active_map_buttons.append(
                Button(
                    (None, y_pos), (300, 50), map_name,
                    color=(60, 60, 60), action=f"load_{map_name}"
                )
            )

    def handle_menu_events(
        self,
        mouse: tuple[int, int],
        event: pygame.event.Event
    ) -> None:
        for btn in self.menu_buttons:
            if btn.is_clicked(mouse, event):
                if btn.action_value == "START_MAP_SELECT":
                    self.win_size = (350, 410)
                    Button.win_size = self.win_size
                    self.center_window()
                    self.screen = pygame.display.set_mode(self.win_size)
                    self.state = 'MAP_SELECT'
                    for diff_btn in self.difficulty_btms:
                        diff_btn.setup_button()
                elif btn.action_value == "QUIT_APP":
                    pygame.quit()
                    sys.exit()

    def handle_map_events(
        self,
        mouse: tuple[int, int],
        event: pygame.event.Event
    ) -> None:
        if not self.selected_difficulty:
            for btn in self.difficulty_btms:
                if btn.is_clicked(mouse, event):
                    self.selected_difficulty = btn.action_value
                    self.create_map_screen()
                    return
        else:
            for m_btn in self.active_map_buttons:
                if m_btn.is_clicked(mouse, event):
                    print(f"Carregando mapa: {m_btn.action_value}")

    def draw_main_menu(self, mouse: tuple[int, int]) -> None:
        TextRenderer.draw_with_outline(
            self.screen, "Fly-in", self.title_font,
            (255, 255, 255), (0, 0, 0),
            (self.win_size[0] / 2, 50), thickness=2
        )
        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font, mouse)

    def draw_map_selection(self, mouse: tuple[int, int]) -> None:
        win_x, _ = self.screen.get_size()
        diff_name = ""
        if self.selected_difficulty:
            diff_name = self.selected_difficulty.split('_')[0].capitalize()

        titulo = ("Choose Difficulty" if not self.selected_difficulty
                  else f"{diff_name}")

        TextRenderer.draw_with_outline(
            self.screen, titulo, self.font,
            (255, 255, 255), (0, 0, 0), (win_x // 2, 40)
        )

        if not self.selected_difficulty:
            for btn in self.difficulty_btms:
                btn.draw(self.screen, self.font, mouse)
        else:
            for m_btn in self.active_map_buttons:
                m_btn.draw(self.screen, self.small_font, mouse)

        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            if self.selected_difficulty:
                self.selected_difficulty = None
                self.active_map_buttons = []
                self.win_size = (350, 410)
                Button.win_size = self.win_size
                self.screen = pygame.display.set_mode(self.win_size)
                for btn in self.difficulty_btms:
                    btn.setup_button()
                pygame.time.delay(150)
            else:
                self.state = 'MAIN_MENU'
                self.win_size = (250, 260)
                Button.win_size = self.win_size
                self.center_window()
                self.screen = pygame.display.set_mode(self.win_size)

    def run(self) -> None:
        clock = pygame.time.Clock()
        while True:
            mouse = pygame.mouse.get_pos()
            self.screen.fill((50, 50, 50))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.state == 'MAIN_MENU':
                    self.handle_menu_events(mouse, event)
                elif self.state == 'MAP_SELECT':
                    self.handle_map_events(mouse, event)

            if self.state == 'MAIN_MENU':
                self.draw_main_menu(mouse)
            elif self.state == 'MAP_SELECT':
                self.draw_map_selection(mouse)

            pygame.display.update()
            clock.tick(60)
