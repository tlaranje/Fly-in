from src.Simulation import Simulation, Visualizer
from src.Parsing import MapParser, DroneMap
from src.Graph import Graph, Dijkstra
from pydantic import ValidationError
from rich import print
import traceback
import sys


def main() -> None:
    try:
        print
        map_parser = MapParser(sys.argv[1])
        drone_map: DroneMap = map_parser.parse()
        graph = Graph(drone_map, main)
        v = Visualizer(graph)
        p = Dijkstra(graph, drone_map)
        s = Simulation(graph, v, p)
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
