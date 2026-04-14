# from src.Simulation import Simulation, Visualizer
from src.Parsing import MapParser, DroneMap
from src.Graph import Dijkstra
from pydantic import ValidationError
from rich import print
import traceback
import sys


def main() -> None:
    try:
        print
        map_parser = MapParser()
        d_map: DroneMap = map_parser.parse(sys.argv[1])
        # g = Graph(drone_map, main)
        # v = Visualizer(d_map)
        # print(d_map.drones)
        p = Dijkstra(d_map)
        start = d_map.start_zone.name
        end = d_map.end_zone.name
        p.find_path(start, end, 0)
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
