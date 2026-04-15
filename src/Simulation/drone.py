from pydantic import BaseModel, Field


class Drone(BaseModel):
    drone_id: int = Field(...)
    curr_zone: str = ""
    path: list[str] = []
    canva_id: int = 0
    drone_tag: str = ""
    delivered: bool = False
    is_moving: bool = False
    blocked: bool = False
    wait_turns: int = 0
    prev_zone: str = ""
    blocked_turns: int = 0
    wait_target: str | None = None
    in_transit_to: str | None = None
    # curr_zone: str | None = None
