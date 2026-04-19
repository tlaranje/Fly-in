from pydantic import BaseModel, model_validator
from typing import Optional, Any
from enum import Enum


class ZoneTypes(Enum):
    """
    Enumerates every zone category with its routing properties.

    Each member stores a three-tuple of ``(name, cost, priority)``
    used by the pathfinding algorithm to weight traversal.

    Members:
        NORMAL: Standard traversable zone with no special rules.
        BLOCKED: Impassable zone; cost is infinite to prevent routing.
        RESTRICTED: Traversable but penalised with a higher cost.
        PRIORITY: Standard cost but elevated scheduling priority.
    """

    NORMAL = ("normal", 1, 0)
    BLOCKED = ("blocked", float("inf"), 0)
    RESTRICTED = ("restricted", 2, 0)
    PRIORITY = ("priority", 1, 1)

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def cost(self) -> int:
        return self.value[1]

    @property
    def priority(self) -> int:
        return self.value[2]


# Flat list of valid string names, used in validation error messages.
VALID_ZONE_TYPES = [zt.name_str for zt in ZoneTypes]


class Zone(BaseModel):
    """Represents a single node in the drone map graph.

    Zones act as vertices in the routing graph.  Each zone has a type
    that controls whether drones may enter it and at what cost, and a
    capacity that limits simultaneous occupancy.

    Attributes:
        name: Unique human-readable identifier for this zone.
        x: World x-coordinate used for rendering and path calculations.
        y: World y-coordinate used for rendering and path calculations.
        zone_type: Routing category; defaults to ``ZoneTypes.NORMAL``.
        color: Optional pygame-compatible color string for the sprite.
        max_drones: Maximum number of drones allowed here at once.
        count_drones: Number of drones currently occupying this zone.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneTypes = ZoneTypes.NORMAL
    color: Optional[str] = None
    max_drones: int = 1
    count_drones: int = 0

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        """
        Validates raw input types and coerces zone_type strings.

        Runs before Pydantic builds the model.  Accepts ``zone_type``
        as either a ``ZoneTypes`` member or a plain string and converts
        the latter to the matching enum member in place.

        Args:
            values: Raw input dictionary passed to the model constructor.

        Returns:
            The (possibly mutated) values dictionary when all checks pass.

        Raises:
            ValueError: Aggregated message listing every detected problem.
        """
        errors = ["Zone errors:"]

        name = values.get("name")

        # name is the primary identifier — must be present and non-blank.
        if name is None:
            errors.append("'name' field is missing")
        elif not isinstance(name, str):
            errors.append("'name' must be a string")
        elif not name.strip():
            errors.append("'name' must not be empty or whitespace")

        # x and y follow identical rules, so validate them together.
        for field in ("x", "y"):
            v = values.get(field)
            if v is None:
                errors.append(f"'{field}' field is missing")
            elif not isinstance(v, int):
                errors.append(f"'{field}' must be an integer")

        zt = values.get("zone_type", ZoneTypes.NORMAL)

        if isinstance(zt, str):
            # Accept lowercase string names from config files and coerce.
            if zt not in VALID_ZONE_TYPES:
                errors.append(
                    f"'zone_type' must be one of {VALID_ZONE_TYPES},"
                    f" got '{zt}'"
                )
            else:
                values["zone_type"] = ZoneTypes[zt.upper()]
        elif not isinstance(zt, ZoneTypes):
            errors.append(
                "'zone_type' must be a string or ZoneTypes enum"
            )

        color = values.get("color")

        # color is optional, but when supplied it must be a non-blank string.
        if color is not None:
            if not isinstance(color, str):
                errors.append("'color' must be a string or None")
            elif not color.strip():
                errors.append("'color' must not be empty or whitespace")

        md = values.get("max_drones", 1)

        # Booleans are ints in Python — exclude them explicitly.
        if isinstance(md, bool) or not isinstance(md, int) or md <= 0:
            errors.append("'max_drones' must be a positive integer")

        canva_id = values.get("canva_id", 0)

        if isinstance(canva_id, bool) or not isinstance(canva_id, int) \
                or canva_id < 0:
            errors.append("'canva_id' must be a non-negative integer")

        count_drones = values.get("count_drones", 0)

        if isinstance(count_drones, bool) \
                or not isinstance(count_drones, int) \
                or count_drones < 0:
            errors.append(
                "'count_drones' must be a non-negative integer"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values

    @model_validator(mode="after")
    def check_logical(self) -> "Zone":
        """
        Validates cross-field logic on the fully constructed model.

        Runs after Pydantic has built the instance.  Ensures that the
        live drone count never exceeds capacity, and that BLOCKED zones
        retain the default capacity of 1 (they are impassable anyway).

        Returns:
            The validated Zone instance when all checks pass.

        Raises:
            ValueError: Aggregated message listing every detected problem.
        """
        errors = ["Zone errors:"]

        # A zone cannot be more occupied than its declared capacity.
        if self.count_drones > self.max_drones:
            errors.append(
                f"'count_drones' ({self.count_drones})"
                f" exceeds 'max_drones' ({self.max_drones})"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return self
