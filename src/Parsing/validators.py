from pydantic import BaseModel, model_validator
from typing import Optional, Any, Self
from src.Simulation import Drone
from enum import Enum


class Zone_Types(Enum):
    # (Name, Cost, priotity)
    NORMAL = ("normal", 1, 0)
    BLOCKED = ("blocked", float("inf"), 0)
    RESTRICTED = ("restricted", 2, 0)
    PRIORITY = ("priority", 1, 1)

    @property
    def name_str(self):
        return self.value[0]

    @property
    def cost(self):
        return self.value[1]

    @property
    def priority(self):
        return self.value[2]


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: Zone_Types = Zone_Types.NORMAL
    color: Optional[str] = None
    max_drones: int = 1
    canva_id: int = 0

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["Zone errors:"]

        # if values is None:
        #     return {}

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
        zt = values.get('zone_type', Zone_Types.NORMAL)
        if isinstance(zt, str):
            if zt not in VALID_ZONE_TYPES:
                errors.append(
                    f"'zone_type' must be one of {VALID_ZONE_TYPES}, "
                    f"got '{zt}'"
                )
            else:
                values['zone_type'] = Zone_Types[zt.upper()]

        elif not isinstance(zt, Zone_Types):
            errors.append("'zone_type' must be a string or Zone_Types enum")

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
    name: str

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["Connection errors:"]

        for field in ('zone1', 'zone2', 'name'):
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
    drones: dict[int, Drone]
    start_zone: Zone
    end_zone: Zone
    zones: dict[str, Zone]
    connections: dict[str, Connection]

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
        # for z in [self.start_hub, self.end_hub] + self.zones:
        # self.zones[z.name] = z
        names = [z for z in self.zones]
        # print([(z.name, _) for z in self.zones.items()])

        if len(names) != len(set(names)):
            errors.append("Zone names must be unique")

        seen = set()

        for c in self.connections.values():
            key = frozenset([c.zone1, c.zone2])

            if key in seen:
                errors.append(f"Duplicate connection: {c.zone1}-{c.zone2}")

            seen.add(key)

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return self
