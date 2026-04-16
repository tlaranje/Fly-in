from pydantic import BaseModel, Field


class Drone(BaseModel):
    drone_id: int = Field(...)
    curr_zone: str = ""
    prev_zone: str = ""
    path: list[str] = []

    # Estado de Movimento (Necessário para Pygame)
    is_moving: bool = False
    target_x: float = 0.0
    target_y: float = 0.0
    should_die: bool = False

    # Lógica de Negócio e Simulação
    delivered: bool = False
    blocked: bool = False
    wait_turns: int = 0
    blocked_turns: int = 0
    wait_target: str | None = None
    in_transit_to: str | None = None
