from .text_renderer import TextRenderer
from src.simulation import Simulation
from pydantic import ValidationError
from .visualizer import Visualizer
from src.parsing import MapParser
from src.dijkstra import Dijkstra
from .button import Button
from rich import print as rprint
import pygame
import sys
import os


class Manager:
    """
    Top-level controller for the main menu and map selection screens.

    Owns the pygame window during the menu phase and hands it off to
    Simulation once the user selects a map.  After the simulation ends
    it reclaims the window and returns to the menu.

    Attributes:
        win_size: Current window dimensions (width, height) in pixels.
        btm_size: Default button dimensions (width, height) in pixels.
        screen: Active pygame display surface.
        state: Active UI state — ``'MAIN_MENU'`` or ``'MAP_SELECT'``.
        selected_difficulty: Key of the currently selected difficulty
            tier, or None if the user is still on the tier list.
        menu_buttons: Buttons shown on the main menu screen.
        diff_to_folder: Maps difficulty state keys to map subfolder names.
        difficulty_btms: Buttons for each difficulty tier.
        maps_data: Discovered map files keyed by difficulty state.
        active_map_buttons: Buttons shown for the selected difficulty.
    """

    def __init__(self) -> None:
        """Initializes pygame, the window, fonts and all button groups."""
        pygame.init()

        self.win_size: tuple[int, int] = (300, 270)
        self.btm_size: tuple[int, int] = (250, 60)
        Button.win_size = self.win_size

        self.center_window()
        self.screen: pygame.Surface = pygame.display.set_mode(self.win_size)
        pygame.display.set_caption("Fly-in")

        # Fonts used across menu screens
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            'arial', 80, bold=True
        )
        self.font: pygame.font.Font = pygame.font.SysFont('arial', 35)
        self.small_font: pygame.font.Font = pygame.font.SysFont('arial', 25)

        self.state: str = 'MAIN_MENU'
        self.selected_difficulty: str | None = None

        self.menu_buttons: list[Button] = [
            Button(
                (None, 110), self.btm_size, "Play", action="START_MAP_SELECT"
            ),
            Button(
                (None, 190), self.btm_size, "Exit", action="QUIT_APP"
            ),
        ]

        # Maps difficulty state key -> maps/ subfolder
        self.diff_to_folder: dict[str, str] = {
            "EASY_MODE": "easy",
            "MEDIUM_MODE": "medium",
            "HARD_MODE": "hard",
            "CHALLENGER_MODE": "challenger",
            "CUSTOM_MODE": "custom",
        }

        self.difficulty_btms: list[Button] = []
        self.setup_difficulty_buttons()

        self.maps_data: dict[str, list[tuple[str, str]]] = (
            self.scan_maps_folder()
        )
        self.active_map_buttons: list[Button] = []

    def scan_maps_folder(self) -> dict[str, list[tuple[str, str]]]:
        """
        Scans the ``maps/`` directory tree for ``.txt`` map files.

        Returns:
            A dict mapping each difficulty state key to a list of
            ``(display_name, full_path)`` tuples, sorted by filename.
        """
        base_path: str = "maps"
        data: dict[str, list[tuple[str, str]]] = {
            key: [] for key in self.diff_to_folder
        }

        for state, folder in self.diff_to_folder.items():
            folder_path: str = os.path.join(base_path, folder)
            if not os.path.exists(folder_path):
                continue

            files: list[str] = sorted(
                f for f in os.listdir(folder_path) if f.endswith('.txt')
            )
            for f in files:
                # Strip numeric prefix and extension, prettify the name
                clean_name: str = f[3:-4].replace('_', ' ').title()
                full_path: str = os.path.join(folder_path, f)
                data[state].append((clean_name, full_path))

        return data

    def setup_difficulty_buttons(self) -> None:
        """Creates one Button per difficulty tier, evenly spaced vertically."""
        difficulties: list[tuple[str, str]] = [
            ("Easy", "EASY_MODE"),
            ("Medium", "MEDIUM_MODE"),
            ("Hard", "HARD_MODE"),
            ("Challenger", "CHALLENGER_MODE"),
            ("Custom", "CUSTOM_MODE"),
        ]
        for i, (label, action) in enumerate(difficulties):
            y_pos: int = 80 + (i * 80)
            self.difficulty_btms.append(
                Button(
                    (None, y_pos), self.btm_size, label, action=action
                )
            )

    def center_window(self) -> None:
        """Asks the OS to centre the window on screen before creation."""
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def update_display_mode(self, width: int, height: int) -> None:
        """Resizes the pygame window and updates Button's shared win_size.

        Args:
            width: New window width in pixels.
            height: New window height in pixels.
        """
        self.win_size = (width, height)
        Button.win_size = self.win_size
        self.screen = pygame.display.set_mode(self.win_size)
        pygame.event.post(
            pygame.event.Event(pygame.ACTIVEEVENT, gain=1, state=1)
        )

    def load_and_start_simulation(self, map_path: str | None) -> None:
        assert map_path is not None

        try:
            map_parser: MapParser = MapParser()
            d_map = map_parser.parse(map_path)

            dijkstra: Dijkstra = Dijkstra(d_map)
            if not dijkstra.is_map_solvable():
                raise ValueError(
                    f"Invalid map: No valid path found from "
                    f"'{d_map.start_zone[0].name}' to "
                    f"'{d_map.end_zone[0].name}'"
                )
            dijkstra.solve()

            viz: Visualizer = Visualizer(d_map)
            sim: Simulation = Simulation(d_map, viz, dijkstra)
            map_name = map_path.split('/')[2].split('.')[0]

            sim.run(map_name)

        except ValidationError as e:
            for error in e.errors():
                msg: str = error['msg'].removeprefix("Value error, ")
                rprint(f"[bold red]{msg}[/bold red]")
        except Exception as e:
            rprint(f"[bold red]{e}[/bold red]")
        finally:
            self.update_display_mode(*self.win_size)
            pygame.display.set_caption("Fly-in")
            pygame.event.clear()

    def create_map_screen(self) -> None:
        """
        Builds the list of map buttons for the selected difficulty tier.

        Resizes the window to fit the number of available maps.
        """
        self.active_map_buttons = []
        maps: list[tuple[str, str]] = self.maps_data.get(
            self.selected_difficulty or "", []
        )

        # Grow the window to fit all map buttons
        new_height: int = 100 + (len(maps) * 70)
        self.update_display_mode(400, new_height)

        for i, (map_name, map_path) in enumerate(maps):
            y_pos: int = 80 + (i * 70)
            self.active_map_buttons.append(
                Button((None, y_pos), (300, 50), map_name, action=map_path)
            )

    def handle_menu_events(
        self,
        mouse: tuple[int, int],
        event: pygame.event.Event,
    ) -> None:
        """
        Processes clicks on the main menu buttons.

        Args:
            mouse: Current mouse position.
            event: The pygame event to inspect.
        """
        for btn in self.menu_buttons:
            if btn.is_clicked(mouse, event):
                if btn.action_value == "START_MAP_SELECT":
                    self.state = 'MAP_SELECT'
                    self.update_display_mode(350, 500)
                    for d_btn in self.difficulty_btms:
                        d_btn.setup_button()
                    pygame.event.clear()
                    return
                elif btn.action_value == "QUIT_APP":
                    pygame.quit()
                    sys.exit()

    def handle_map_events(
        self,
        mouse: tuple[int, int],
        event: pygame.event.Event,
    ) -> None:
        """
        Processes clicks on difficulty / map buttons and ESC navigation.

        Args:
            mouse: Current mouse position.
            event: The pygame event to inspect.
        """
        if not self.selected_difficulty:
            # Show difficulty tier list
            for btn in self.difficulty_btms:
                if btn.is_clicked(mouse, event):
                    self.selected_difficulty = btn.action_value
                    self.create_map_screen()
                    pygame.event.clear()
                    return
        else:
            # Show map list for the selected tier
            for m_btn in self.active_map_buttons:
                if m_btn.is_clicked(mouse, event):
                    self.load_and_start_simulation(m_btn.action_value)

        # ESC navigates one level up
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.selected_difficulty:
                # Go back to tier list
                self.selected_difficulty = None
                self.active_map_buttons = []
                self.update_display_mode(350, 500)
                for btn in self.difficulty_btms:
                    btn.setup_button()
            else:
                # Go back to main menu
                self.state = 'MAIN_MENU'
                self.update_display_mode(300, 270)

    def draw_main_menu(self, mouse: tuple[int, int]) -> None:
        """
        Renders the main menu title and buttons.

        Args:
            mouse: Current mouse position, forwarded to buttons for hover.
        """
        TextRenderer.draw_with_outline(
            self.screen, "Fly-in", self.title_font,
            (255, 255, 255), (0, 0, 0),
            (self.win_size[0] // 2, 50), thickness=2,
        )
        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font, mouse)

    def draw_map_selection(self, mouse: tuple[int, int]) -> None:
        """
        Renders either the difficulty tier list or the map list.

        Args:
            mouse: Current mouse position, forwarded to buttons for hover.
        """
        win_x: int = self.screen.get_size()[0]

        if self.selected_difficulty:
            titulo: str = (
                self.selected_difficulty.split('_')[0].capitalize()
            )
        else:
            titulo = "Choose Difficulty"

        TextRenderer.draw_with_outline(
            self.screen, titulo, self.font,
            (255, 255, 255), (0, 0, 0), (win_x // 2, 40),
        )

        if not self.selected_difficulty:
            for btn in self.difficulty_btms:
                btn.draw(self.screen, self.font, mouse)
        else:
            for m_btn in self.active_map_buttons:
                m_btn.draw(self.screen, self.small_font, mouse)

    def run(self) -> None:
        """
        Enters the manager's main event loop (menu phase).

        Dispatches events to the active screen handler and redraws
        at 60 fps until the application quits.
        """
        clock: pygame.time.Clock = pygame.time.Clock()

        while True:
            mouse: tuple[int, int] = pygame.mouse.get_pos()

            for event in pygame.event.get():
                # Global quit — ESC on main menu posts a QUIT event
                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_ESCAPE
                        and self.state == 'MAIN_MENU'
                    ):
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
