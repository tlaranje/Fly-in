from src.Simulation import Simulation, Visualizer
from src.Parsing import MapParser, DroneMap
from src.Graph import Dijkstra
from pydantic import ValidationError
from rich import print
import traceback
import pygame
import sys


def main() -> None:
    try:
        print
        map_parser = MapParser()
        d_map: DroneMap = map_parser.parse(sys.argv[1])
        d = Dijkstra(d_map)
        results, total_turns = d.solve()
        v = Visualizer(d_map)
        s = Simulation(d_map, v, d)
        s.run()
    except ValidationError as e:
        for error in e.errors():
            msg = error['msg'].removeprefix("Value error, ")
            print(f"[bold red]{msg}[/bold red]")
    except Exception:
        print("[bold red]Erro inesperado:[/bold red]")
        traceback.print_exc()


if __name__ == "__main__":

    # Initialize Pygame
    pygame.init()

    # Set up the game window
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Hello Pygame")

    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    # Quit Pygame
    pygame.quit()
    # main()
