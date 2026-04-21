from pydantic import BaseModel, model_validator
from .connection import Connection
from .drone import Drone
from typing import Any, Self
from .zone import Zone


class DroneMap(BaseModel):
    """
    Represents the full drone simulation map.

    Holds the fleet of drones, the zone graph and the connections
    between zones. Both validators run in sequence: the ``before``
    pass checks raw input types and counts, then the ``after`` pass
    verifies cross-field consistency on the fully constructed model.

    Attributes:
        nb_drones: Total number of drones in the simulation.
        drones: Mapping of drone ID to a (Drone, pygame rect) tuple.
        start_zone: Entry point of the map as a (Zone, pygame rect) tuple.
        end_zone: Exit point of the map as a (Zone, pygame rect) tuple.
        zones: Mapping of zone name to a (Zone, pygame rect) tuple.
        connections: Mapping of connection name to its Connection model.
    """

    nb_drones: int
    drones: dict[int, tuple[Drone, Any]]
    start_zone: tuple[Zone, Any]
    end_zone: tuple[Zone, Any]
    zones: dict[str, tuple[Zone, Any]]
    connections: dict[str, Connection]

    @model_validator(mode="before")
    @classmethod
    def check_fields(cls, values: dict[str, Any]) -> Any:
        """
        Validates raw input types and structural constraints.

        Runs before Pydantic builds the model, so all values are still
        in their raw dict form.  Checks that ``nb_drones`` is a positive
        integer, that the ``drones`` dict has the expected keys, that
        ``zones`` contains at least two entries, and that ``connections``
        is a dict when provided.

        Args:
            values: Raw input dictionary passed to the model constructor.

        Returns:
            The original values dictionary when all checks pass.

        Raises:
            ValueError: Aggregated message listing every detected problem.
        """
        errors = ["DroneMap errors:"]

        nb = values.get("nb_drones")

        # nb_drones must exist and be a positive integer.
        if nb is None:
            errors.append("'nb_drones' is not define in file map")
        elif not isinstance(nb, int) or nb <= 0:
            errors.append("'nb_drones' must be a positive integer")

        drones = values.get("drones")

        if not isinstance(drones, dict):
            errors.append("'drones' must be a dict")
        else:
            # The fleet size must match the declared drone count.
            if len(drones) != nb:
                errors.append(
                    f"'drones' must have exactly 'nb_drones' ({nb})"
                    f" entries, got {len(drones)}"
                )

            # Keys must form the contiguous range 0 … nb_drones-1.
            if nb and set(drones.keys()) != set(range(nb)):
                errors.append(
                    "'drones' keys must be integers"
                    " from 0 to nb_drones-1"
                )

        zones = values.get("zones")

        # A valid map needs at least a start zone and an end zone.
        if not isinstance(zones, dict) or len(zones) < 2:
            errors.append(
                "'zones' must be a dict with at least 2 zones"
            )

        connections = values.get("connections")

        # connections is optional, but must be a dict when supplied.
        if connections is not None and not isinstance(connections, dict):
            errors.append("'connections' must be a dict")

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return values

    @model_validator(mode="after")
    def check_map(self) -> Self:
        """
        Validates cross-field consistency on the built model.

        Runs after Pydantic has constructed the model instance.
        Checks that zone names are unique, that start and end zones
        exist and differ, that every connection references known zones,
        that no duplicate or self-referencing connections exist, that
        no zone is completely isolated from the graph, and that a
        connected path exists from the start zone to the end zone.

        Returns:
            The validated model instance when all checks pass.

        Raises:
            ValueError: Aggregated message listing every detected problem.
        """
        errors = ["DroneMap errors:"]

        names = list(self.zones.keys())

        # Zone names are used as dict keys, but validate explicitly anyway.
        if len(names) != len(set(names)):
            errors.append("Zone names must be unique")

        valid_zone_names = set(self.zones.keys())
        start_name = self.start_zone[0].name
        end_name = self.end_zone[0].name

        # start_zone and end_zone must point to registered zones.
        if start_name not in valid_zone_names:
            errors.append(
                f"start_zone '{start_name}' not found in zones"
            )
        if end_name not in valid_zone_names:
            errors.append(
                f"end_zone '{end_name}' not found in zones"
            )

        # A map where start equals end would make routing trivial/broken.
        if start_name == end_name:
            errors.append("start_zone and end_zone must be different")

        # Track seen zone pairs to detect duplicates and connected zones.
        seen: set[frozenset[str]] = set()
        connected_zones: set[str] = set()

        for conn_name, c in self.connections.items():

            # Self-loops are meaningless in a drone routing context.
            if c.zone1 == c.zone2:
                errors.append(
                    f"Connection '{conn_name}' connects"
                    f" zone '{c.zone1}' to itself"
                )
                continue

            # Both endpoints must exist in the zone registry.
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

            # Parallel edges between the same pair of zones are not allowed.
            if key in seen:
                errors.append(
                    f"Duplicate connection"
                    f" between '{c.zone1}' and '{c.zone2}'"
                )
            seen.add(key)

            connected_zones.add(c.zone1)
            connected_zones.add(c.zone2)

        isolated = valid_zone_names - connected_zones

        # Every zone must participate in at least one connection.
        if isolated:
            errors.append(
                f"Isolated zones with no connections: {isolated}"
            )

        if len(errors) > 1:
            raise ValueError("\n    ".join(errors))

        return self
