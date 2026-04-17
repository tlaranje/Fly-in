from pydantic import BaseModel, model_validator
from typing import Optional, Any
from enum import Enum


class ZoneTypes(Enum):
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


VALID_ZONE_TYPES = [zt.name_str for zt in ZoneTypes]


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: ZoneTypes = ZoneTypes.NORMAL
    color: Optional[str] = None
    max_drones: int = 1
    canva_id: int = 0
    count_drones: int = 0

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["Zone errors:"]

        name = values.get('name')
        if name is None:
            errors.append("'name' field is missing")
        elif not isinstance(name, str):
            errors.append("'name' must be a string")
        elif not name.strip():
            errors.append("'name' must not be empty or whitespace")

        for field in ('x', 'y'):
            v = values.get(field)
            if v is None:
                errors.append(f"'{field}' field is missing")
            elif not isinstance(v, int):
                errors.append(f"'{field}' must be an integer")

        zt = values.get('zone_type', ZoneTypes.NORMAL)
        if isinstance(zt, str):
            if zt not in VALID_ZONE_TYPES:
                errors.append(
                    f"'zone_type' must be one of {VALID_ZONE_TYPES},"
                    f" got '{zt}'"
                )
            else:
                values['zone_type'] = ZoneTypes[zt.upper()]
        elif not isinstance(zt, ZoneTypes):
            errors.append(
                "'zone_type' must be a string or ZoneTypes enum"
            )

        color = values.get('color')
        if color is not None:
            if not isinstance(color, str):
                errors.append("'color' must be a string or None")
            elif not color.strip():
                errors.append("'color' must not be empty or whitespace")

        md = values.get('max_drones', 1)
        if not isinstance(md, int) or md <= 0:
            errors.append("'max_drones' must be a positive integer")

        canva_id = values.get('canva_id', 0)
        if not isinstance(canva_id, int) or canva_id < 0:
            errors.append("'canva_id' must be a non-negative integer")

        count_drones = values.get('count_drones', 0)
        if not isinstance(count_drones, int) or count_drones < 0:
            errors.append(
                "'count_drones' must be a non-negative integer"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return values

    @model_validator(mode="after")
    def check_logical(self) -> "Zone":
        errors = ["Zone errors:"]

        if self.count_drones > self.max_drones:
            errors.append(
                f"'count_drones' ({self.count_drones})"
                f" exceeds 'max_drones' ({self.max_drones})"
            )

        if (
            self.zone_type == ZoneTypes.BLOCKED
            and self.max_drones != 1
        ):
            errors.append(
                "'max_drones' should be 1 for BLOCKED zones"
                " as they are impassable"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return self
