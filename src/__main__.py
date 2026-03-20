from src.Parsing.validators import Zone
from rich import print
from pydantic import ValidationError


def main() -> None:
    try:
        """ Zone(
            name="Hub",
            x=0,
            y=0,
            zone_type="normal",
            max_drones=1
        ) """
        Zone()
    except ValidationError as e:
        for error in e.errors():
            msg = error['msg'].removeprefix("Value error, ")
            print(f"[bold red]{msg}[/bold red]")


if __name__ == "__main__":
    main()
