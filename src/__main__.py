from src.Parsing.parse_maps import MapParser
from src.Parsing.validators import DroneMap
from src.Graph.graph import Graph
from src.Graph.pathfinder import PathFinder
from pydantic import ValidationError
from rich import print
import sys


def main() -> None:
    try:
        map_parser = MapParser(sys.argv[1])
        drone_map: DroneMap = map_parser.parse()
        graph = Graph(drone_map)
        path_finder = PathFinder(graph, drone_map)
        shortest_path = path_finder.find_shortest_path()
        print(shortest_path)
    except ValidationError as e:
        for error in e.errors():
            msg = error['msg'].removeprefix("Value error, ")
            print(f"[bold red]{msg}[/bold red]")
    except Exception as e:
        print(f"[bold red]{e}[/bold red]")


if __name__ == "__main__":
    main()
