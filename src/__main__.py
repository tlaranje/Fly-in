from src.Visualizer import Visualizer, GameManager
from src.Simulation import Simulation
from pydantic import ValidationError
from src.parsing import MapParser
from src.dijkstra import Dijkstra
from src.core import DroneMap
from rich import print
import traceback
import sys


def main() -> None:
    try:
        print
        map_parser = MapParser()
        d_map: DroneMap = map_parser.parse(sys.argv[1])
        d = Dijkstra(d_map)
        d.solve()
        v = Visualizer(d_map)
        s = Simulation(d_map, v, d)
        game = GameManager()
        game.run()
        s.run()
    except ValidationError as e:
        for error in e.errors():
            msg = error['msg'].removeprefix("Value error, ")
            print(f"[bold red]{msg}[/bold red]")
    except Exception:
        print("[bold red]Erro inesperado:[/bold red]")
        traceback.print_exc()


if __name__ == "__main__":
    main()
