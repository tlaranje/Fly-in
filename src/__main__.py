from src.visualizer import Manager
from pydantic import ValidationError
from rich import print as rprint
import pygame


def main() -> None:
    """
    Entry point for the Fly-in drone simulation application.

    Initializes the Manager, which handles the main menu and
    delegates to the simulation once a map is selected.

    Raises caught exceptions with formatted console output:
        ValidationError: Shown when a map file has invalid structure.
        Exception: Any other unexpected error prints a full traceback.
    """
    try:
        game: Manager = Manager()
        game.run()

    except ValidationError as e:
        for error in e.errors():
            msg: str = error['msg'].removeprefix("Value error, ")
            rprint(f"[bold red]{msg}[/bold red]")

    except Exception:
        rprint("[bold red]Erro inesperado:[/bold red]")

    finally:
        # Always quit pygame cleanly, even if an exception was raised
        pygame.quit()


if __name__ == "__main__":
    main()
