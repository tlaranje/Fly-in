from src.visualizer import Manager
from pydantic import ValidationError
from rich import print
import traceback
import pygame


def main() -> None:
    try:
        game = Manager()
        game.run()

    except ValidationError as e:
        for error in e.errors():
            msg = error['msg'].removeprefix("Value error, ")
            print(f"[bold red]{msg}[/bold red]")
    except Exception:
        print("[bold red]Erro inesperado:[/bold red]")
        traceback.print_exc()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
