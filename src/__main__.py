from src.Simulation import Simulation, Visualizer
from src.Parsing import MapParser, DroneMap
from pydantic import ValidationError
from src.Graph import Graph, PathFinder
from rich import print
import sys
import traceback


def main() -> None:
    try:
        map_parser = MapParser(sys.argv[1])
        drone_map: DroneMap = map_parser.parse()
        graph = Graph(drone_map)
        v = Visualizer(graph)
        p = PathFinder(graph, drone_map)
        p.find_alternative_path()
        # s = Simulation(graph, v, p)
        # s.run()
    except ValidationError as e:
        for error in e.errors():
            msg = error['msg'].removeprefix("Value error, ")
            print(f"[bold red]{msg}[/bold red]")
    except Exception:
        print("[bold red]Erro inesperado:[/bold red]")
        traceback.print_exc()


if __name__ == "__main__":
    main()
