from pydantic import BaseModel, model_validator
from typing import Any


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
            elif not v.strip():
                errors.append(f"'{field}' must not be empty or whitespace")

        zone1 = values.get('zone1')
        zone2 = values.get('zone2')
        if (
            isinstance(zone1, str)
            and isinstance(zone2, str)
            and zone1.strip() == zone2.strip()
        ):
            errors.append("'zone1' and 'zone2' must be different zones")

        mlc = values.get('max_link_capacity', 1)
        if not isinstance(mlc, int) or mlc <= 0:
            errors.append(
                "'max_link_capacity' must be a positive integer"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return values
