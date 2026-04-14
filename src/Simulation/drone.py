from pydantic import BaseModel, Field


class Drone(BaseModel):
    drone_id: int = Field(...)
    drone_tag: str = ""
    curr_zone: str | None = None
    canva_id: int = 0
    path: list[str] = []
    delivered: bool = False
    is_moving: bool = False
    blocked: bool = False
    wait_turns: int = 0
    prev_zone: str = ""
    blocked_turns: int = 0
    wait_target: str | None = None
    in_transit_to: str | None = None
    schedule: list[tuple[str, int]] = []
    schedule_index: int = 0
