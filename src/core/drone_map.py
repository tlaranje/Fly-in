from pydantic import BaseModel, model_validator
from .connection import Connection
from .drone import Drone
from typing import Any, Self
from .zone import Zone


class DroneMap(BaseModel):
    nb_drones: int
    drones: dict[int, tuple[Drone, Any]]
    start_zone: tuple[Zone, Any]
    end_zone: tuple[Zone, Any]
    zones: dict[str, tuple[Zone, Any]]
    connections: dict[str, Connection]

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        errors = ["DroneMap errors:"]

        nb = values.get('nb_drones')
        if nb is None or not isinstance(nb, int) or nb <= 0:
            errors.append(
                "'nb_drones' must be a positive integer"
            )

        drones = values.get('drones')
        if not isinstance(drones, dict):
            errors.append("'drones' must be a dict")
        else:
            if len(drones) != nb:
                errors.append(
                    f"'drones' must have exactly 'nb_drones' ({nb})"
                    f" entries, got {len(drones)}"
                )
            if nb and set(drones.keys()) != set(range(nb)):
                errors.append(
                    "'drones' keys must be integers"
                    " from 0 to nb_drones-1"
                )

        zones = values.get('zones')
        if not isinstance(zones, dict) or len(zones) < 2:
            errors.append(
                "'zones' must be a dict with at least 2 zones"
            )

        connections = values.get('connections')
        if connections is not None and not isinstance(connections, dict):
            errors.append("'connections' must be a dict")

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return values

    @model_validator(mode="after")
    def check_unique_names(self) -> Self:
        errors = ["DroneMap errors:"]

        names = list(self.zones.keys())
        if len(names) != len(set(names)):
            errors.append("Zone names must be unique")

        valid_zone_names = set(self.zones.keys())

        start_name = self.start_zone[0].name
        end_name = self.end_zone[0].name

        if start_name not in valid_zone_names:
            errors.append(
                f"start_zone '{start_name}' not found in zones"
            )
        if end_name not in valid_zone_names:
            errors.append(
                f"end_zone '{end_name}' not found in zones"
            )
        if start_name == end_name:
            errors.append(
                "start_zone and end_zone must be different"
            )

        seen = set()
        connected_zones = set()

        for conn_name, c in self.connections.items():
            if c.zone1 == c.zone2:
                errors.append(
                    f"Connection '{conn_name}' connects"
                    f" zone '{c.zone1}' to itself"
                )
                continue

            if c.zone1 not in valid_zone_names:
                errors.append(
                    f"Connection '{conn_name}' references"
                    f" unknown zone: '{c.zone1}'"
                )
            if c.zone2 not in valid_zone_names:
                errors.append(
                    f"Connection '{conn_name}' references"
                    f" unknown zone: '{c.zone2}'"
                )

            key = frozenset([c.zone1, c.zone2])
            if key in seen:
                errors.append(
                    f"Duplicate connection"
                    f" between '{c.zone1}' and '{c.zone2}'"
                )
            seen.add(key)

            connected_zones.add(c.zone1)
            connected_zones.add(c.zone2)

        isolated = valid_zone_names - connected_zones
        if isolated:
            errors.append(
                f"Isolated zones with no connections: {isolated}"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))
        return self
