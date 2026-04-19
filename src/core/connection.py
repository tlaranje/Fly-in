from pydantic import BaseModel, model_validator
from typing import Any


class Connection(BaseModel):
    """
    Represents a directional link between two zones in the drone map.

    Attributes:
        zone1: Name of the first zone.
        zone2: Name of the second zone.
        max_link_capacity: Maximum number of drones allowed on the link
            simultaneously. Defaults to 1.
        name: Unique identifier for this connection.
    """
    zone1: str
    zone2: str
    max_link_capacity: int = 1
    name: str

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        """
        Validates all fields before the model is instantiated.

        Ensures required string fields are present, non-empty and of the
        correct type, that zone1 and zone2 are distinct, and that
        max_link_capacity is a positive integer.

        Args:
            values: Raw input dictionary passed to the model constructor.

        Returns:
            The original values dictionary when all checks pass.

        Raises:
            ValueError: If one or more validation rules are violated.
                The message lists every detected problem.
        """
        errors = ["Connection errors:"]

        # Validate required string fields: presence, type and content.
        for field in ("zone1", "zone2", "name"):
            v = values.get(field)

            if v is None:
                errors.append(f"'{field}' field is missing.")
            elif not isinstance(v, str):
                errors.append(f"'{field}' must be a string")
            elif not v.strip():
                errors.append(
                    f"'{field}' must not be empty or whitespace"
                )

        zone1 = values.get("zone1")
        zone2 = values.get("zone2")

        # Both zones must refer to different locations.
        if (
            isinstance(zone1, str)
            and isinstance(zone2, str)
            and zone1.strip() == zone2.strip()
        ):
            errors.append("'zone1' and 'zone2' must be different zones")

        mlc = values.get("max_link_capacity", 1)

        # Capacity must be a positive integer (booleans are excluded).
        if not isinstance(mlc, int) or isinstance(mlc, bool) or mlc <= 0:
            errors.append(
                "'max_link_capacity' must be a positive integer"
            )

        # Raise a single aggregated error when any check failed.
        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values
