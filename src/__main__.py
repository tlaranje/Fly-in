from src.Simulation import Simulation, Visualizer
from src.Parsing import MapParser, DroneMap
from pydantic import ValidationError
from src.Graph import Graph
from rich import print
import sys
import traceback


def main() -> None:
    try:
        map_parser = MapParser(sys.argv[1])
        drone_map: DroneMap = map_parser.parse()
        graph = Graph(drone_map)
        v = Visualizer(graph)
        s = Simulation(graph, v)
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
