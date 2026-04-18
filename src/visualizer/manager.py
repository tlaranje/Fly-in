import pygame
import sys
import os
from .text_renderer import TextRenderer
from .button import Button
from src.parsing import MapParser
from src.dijkstra import Dijkstra
from src.simulation import Simulation
from .visualizer import Visualizer


class Manager:
    def __init__(self) -> None:
        pygame.init()
        self.win_size: tuple[int, int] = (300, 270)
        Button.win_size = self.win_size
        self.btm_size: tuple[int, int] = (250, 60)
        self.center_window()
        self.screen: pygame.Surface = pygame.display.set_mode(self.win_size)
        pygame.display.set_caption("Fly-in")

        self.title_font = pygame.font.SysFont('arial', 80, bold=True)
        self.font = pygame.font.SysFont('arial', 35)
        self.small_font = pygame.font.SysFont('arial', 25)

        self.state = 'MAIN_MENU'
        self.selected_difficulty: str | None = None
        self.menu_buttons: list[Button] = [
            Button((None, 110), self.btm_size, "Play",
                   action="START_MAP_SELECT"),
            Button((None, 190), self.btm_size, "Exit",
                   action="QUIT_APP")
        ]

        self.diff_to_folder = {
            "EASY_MODE": "easy",
            "MEDIUM_MODE": "medium",
            "HARD_MODE": "hard",
            "CHALLENGER_MODE": "challenger",
            "CUSTOM_MODE": "custom"
        }

        self.difficulty_btms: list[Button] = []
        self.setup_difficulty_buttons()

        self.maps_data = self.scan_maps_folder()
        self.active_map_buttons: list[Button] = []

    def scan_maps_folder(self) -> dict[str, list[tuple[str, str]]]:
        base_path = "maps"
        data: dict = {key: [] for key in self.diff_to_folder}

        for state, folder in self.diff_to_folder.items():
            folder_path = os.path.join(base_path, folder)
            if not os.path.exists(folder_path):
                continue

            files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith('.txt')]
            )

            for f in files:
                clean_name = f[3:-4].replace('_', ' ').title()
                full_path = os.path.join(folder_path, f)
                data[state].append((clean_name, full_path))

        return data

    def setup_difficulty_buttons(self) -> None:
        difficulties = [
            ("Easy", "EASY_MODE"),
            ("Medium", "MEDIUM_MODE"),
            ("Hard", "HARD_MODE"),
            ("Challenger", "CHALLENGER_MODE"),
            ("Custom", "CUSTOM_MODE")
        ]
        for i, (nome, acao) in enumerate(difficulties):
            y_pos = 80 + (i * 80)
            self.difficulty_btms.append(
                Button((None, y_pos), self.btm_size, nome, action=acao)
            )

    def center_window(self) -> None:
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def update_display_mode(self, width: int, height: int) -> None:
        self.win_size = (width, height)
        Button.win_size = self.win_size
        self.screen = pygame.display.set_mode(self.win_size)

    def load_and_start_simulation(self, map_path: str | None) -> None:
        assert map_path is not None

        try:
            map_parser = MapParser()
            d_map = map_parser.parse(map_path)

            dijkstra = Dijkstra(d_map)
            dijkstra.solve()

            viz = Visualizer(d_map)
            sim = Simulation(d_map, viz, dijkstra)

            sim.run()

            self.update_display_mode(self.win_size[0], self.win_size[1])
            pygame.display.set_caption("Fly-in")

        except Exception as e:
            print(f"Erro ao carregar mapa {map_path}: {e}")

    def create_map_screen(self) -> None:
        self.active_map_buttons = []
        maps = self.maps_data.get(self.selected_difficulty or "", [])

        new_height = 100 + (len(maps) * 70)
        self.update_display_mode(400, new_height)

        for i, (map_name, map_path) in enumerate(maps):
            y_pos = 80 + (i * 70)
            self.active_map_buttons.append(
                Button(
                    (None, y_pos), (300, 50), map_name,
                    color=(60, 60, 60), action=map_path
                )
            )

    def handle_menu_events(
            self, mouse: tuple[int, int], event: pygame.event.Event
    ) -> None:
        for btn in self.menu_buttons:
            if btn.is_clicked(mouse, event):
                if btn.action_value == "START_MAP_SELECT":
                    self.state = 'MAP_SELECT'
                    self.update_display_mode(350, 500)
                    for d_btn in self.difficulty_btms:
                        d_btn.setup_button()
                elif btn.action_value == "QUIT_APP":
                    pygame.quit()
                    sys.exit()

    def handle_map_events(
            self, mouse: tuple[int, int], event: pygame.event.Event
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
                    self.load_and_start_simulation(m_btn.action_value)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.selected_difficulty:
                self.selected_difficulty = None
                self.active_map_buttons = []
                self.update_display_mode(350, 500)
                for btn in self.difficulty_btms:
                    btn.setup_button()
            else:
                self.state = 'MAIN_MENU'
                self.update_display_mode(300, 270)

    def draw_main_menu(self, mouse: tuple[int, int]) -> None:
        TextRenderer.draw_with_outline(
            self.screen, "Fly-in", self.title_font,
            (255, 255, 255), (0, 0, 0),
            (self.win_size[0] // 2, 50), thickness=2
        )
        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font, mouse)

    def draw_map_selection(self, mouse: tuple[int, int]) -> None:
        win_x, _ = self.screen.get_size()
        diff_name = ""
        if self.selected_difficulty:
            diff_name = self.selected_difficulty.split('_')[0].capitalize()

        titulo = "Choose Difficulty" if not self.selected_difficulty \
            else f"{diff_name}"

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

    def run(self) -> None:
        clock = pygame.time.Clock()
        while True:
            mouse = pygame.mouse.get_pos()
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == 'MAIN_MENU':
                    self.handle_menu_events(mouse, event)
                elif self.state == 'MAP_SELECT':
                    self.handle_map_events(mouse, event)

            self.screen.fill((50, 50, 50))

            if self.state == 'MAIN_MENU':
                self.draw_main_menu(mouse)
            elif self.state == 'MAP_SELECT':
                self.draw_map_selection(mouse)

            pygame.display.flip()
            clock.tick(60)
