from pydantic import BaseModel, model_validator, ValidationError
from typing import Optional, Any


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = 1

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["Zone errors:"]

        name = values.get('name')
        if name is None:
            errors.append("'name' field is missing.")
        elif not isinstance(name, str):
            errors.append("'name' must be a string")

        x = values.get('x')
        if x is None:
            errors.append("'x' field is missing.")
        elif not isinstance(x, int):
            errors.append("'x' must be a integer")

        y = values.get('y')
        if y is None:
            errors.append("'y' field is missing.")
        elif not isinstance(y, int):
            errors.append("'y' must be a integer")

        VALID_ZONE_TYPES = ["normal", "blocked", "restricted", "priority"]
        zt = values.get('zone_type')
        if zt is None:
            errors.append("'zone_type' field is missing.")
        elif zt not in VALID_ZONE_TYPES:
            errors.append(
                f"'zone_type' must be one of {VALID_ZONE_TYPES}, got '{zt}'"
            )

        color = values.get('color')
        if color is not None and not isinstance(color, str):
            errors.append("'color' must be a string or None")

        md = values.get('max_drones')
        if md is None:
            errors.append("'max_drones' field is missing.")
        elif not isinstance(md, int) or md <= 0:
            errors.append("'max_drones' must be a positive integer")

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values
