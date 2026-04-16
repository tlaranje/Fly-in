from src.Simulation import Simulation, Visualizer
from src.Parsing import MapParser, DroneMap
from pydantic import ValidationError
from src.Graph import Dijkstra
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
