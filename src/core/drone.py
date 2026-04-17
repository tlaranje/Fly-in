from pydantic import BaseModel, Field, model_validator
from typing import Any


class Drone(BaseModel):
    drone_id: int = Field(...)
    curr_zone: str = ""
    path: list[str] = []
    is_moving: bool = False
    target_x: float = 0.0
    target_y: float = 0.0
    should_die: bool = False

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["Drone errors:"]

        drone_id = values.get('drone_id')
        if drone_id is None:
            errors.append("'drone_id' field is missing")
        elif not isinstance(drone_id, int):
            errors.append("'drone_id' must be an integer")
        elif drone_id < 0:
            errors.append("'drone_id' must be a non-negative integer")

        curr_zone = values.get('curr_zone', "")
        if not isinstance(curr_zone, str):
            errors.append("'curr_zone' must be a string")

        path = values.get('path', [])
        if not isinstance(path, list):
            errors.append("'path' must be a list")
        elif not all(isinstance(z, str) for z in path):
            errors.append("'path' entries must all be strings")

        for field in ('is_moving', 'should_die'):
            v = values.get(field, False)
            if not isinstance(v, bool):
                errors.append(f"'{field}' must be a boolean")

        for field in ('target_x', 'target_y'):
            v = values.get(field, 0.0)
            if not isinstance(v, (int, float)):
                errors.append(f"'{field}' must be a number")

        is_moving = values.get('is_moving', False)
        if isinstance(is_moving, bool) and is_moving:
            if isinstance(path, list) and len(path) == 0:
                errors.append(
                    "'is_moving' is True but 'path' is empty"
                )
            if isinstance(curr_zone, str) and not curr_zone.strip():
                errors.append(
                    "'is_moving' is True but 'curr_zone' is empty"
                )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return values
