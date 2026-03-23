from pydantic import BaseModel, model_validator
from typing import Optional, Any, Self


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
        zt = values.get('zone_type', 'normal')
        if zt not in VALID_ZONE_TYPES:
            errors.append(
                f"'zone_type' must be one of {VALID_ZONE_TYPES}, got '{zt}'"
            )

        color = values.get('color')
        if color is not None and not isinstance(color, str):
            errors.append("'color' must be a string or None")

        md = values.get('max_drones', 1)
        if not isinstance(md, int) or md <= 0:
            errors.append("'max_drones' must be a positive integer")

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values


class Connection(BaseModel):
    zone1: str
    zone2: str
    max_link_capacity: int = 1

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["Connection errors:"]

        for field in ('zone1', 'zone2'):
            v = values.get(field)
            if v is None:
                errors.append(f"'{field}' field is missing.")
            elif not isinstance(v, str):
                errors.append(f"'{field}' must be a string")

        mlc = values.get('max_link_capacity', 1)
        if not isinstance(mlc, int) or mlc <= 0:
            errors.append("'max_link_capacity' must be a positive integer")

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values


class DroneMap(BaseModel):
    nb_drones: int
    start_hub: Zone
    end_hub: Zone
    hubs: list[Zone] = []
    connections: list[Connection] = []

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["DroneMap errors:"]

        nb = values.get('nb_drones')
        if nb is None or not isinstance(nb, int) or nb <= 0:
            errors.append("'nb_drones' must be a positive integer")

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values

    @model_validator(mode="after")
    def check_unique_names(self) -> Self:
        errors = ["DroneMap errors:"]
        all_zones = [self.start_hub, self.end_hub] + self.hubs
        names = [z.name for z in all_zones]
        if len(names) != len(set(names)):
            errors.append("Zone names must be unique")

        seen = set()
        for c in self.connections:
            key = frozenset([c.zone1, c.zone2])
            if key in seen:
                errors.append(f"Duplicate connection: {c.zone1}-{c.zone2}")
            seen.add(key)
        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return self
