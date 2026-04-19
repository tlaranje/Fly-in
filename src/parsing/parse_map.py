from src.core import DroneMap, Zone, Connection, Drone
from typing import Any
import re

# Matches a zone line of the form:
#   <prefix>: <name> <x> <y> [optional metadata]
_ZONE_PATTERN = re.compile(r"""
    ^\w+:              # line starts with a zone type prefix
    \s+(\S+)\s+        # whitespace + zone name + whitespace
    (-?\d+)\s+(-?\d+)  # x coordinate + whitespace + y coordinate
    (?:                # optional metadata block
        \s+\[          # whitespace + opening bracket
        ([^\]]*)\]     # metadata content + closing bracket
    )?
""", re.VERBOSE)

# Matches a connection line of the form:
#   connection: <zone1>-<zone2> [optional metadata]
_CONN_PATTERN = re.compile(r"""
    ^connection:      # line starts with connection:
    \s+([^-\s]+)-     # whitespace + first zone name + separator
    ([^-\s]+)         # second zone name
    (?:               # optional metadata block
        \s+\[         # whitespace + opening bracket
        ([^\]]*)\]    # metadata content + closing bracket
    )?
""", re.VERBOSE)


class MapParser:
    """
    Parses a plain-text map file into a validated DroneMap instance.

    The file format uses prefixed lines to declare zones and connections.
    Lines beginning with ``#`` are treated as comments and skipped.

    Supported line prefixes:
        - ``nb_drones``: declares the total fleet size.
        - ``start_hub``: declares the start zone.
        - ``end_hub``: declares the end zone.
        - ``hub``: declares an intermediate zone.
        - ``connection``: declares a link between two zones.
    """

    def _parse_metadata(self, raw_metadata: str | None) -> dict[str, Any]:
        """
        Parses an inline metadata string into a key-value dictionary.

        Metadata appears inside square brackets as space-separated
        ``key=value`` pairs, e.g. ``[zone=restricted max_drones=2]``.

        Args:
            raw_metadata: The raw string captured from inside the brackets,
                or None when the metadata block is absent.

        Returns:
            A dictionary of parsed key-value pairs, or an empty dict when
            the input is None or contains no ``=`` tokens.
        """
        if raw_metadata is None:
            return {}

        parsed: dict[str, Any] = {}

        # Each token is a key=value pair; tokens without '=' are ignored.
        for token in raw_metadata.split(" "):
            if "=" in token:
                key, _, value = token.partition("=")
                parsed[key] = value

        return parsed

    def _build_zone(self, line: str) -> tuple[str, Zone] | None:
        """
        Parses a hub line and constructs a Zone instance.

        Handles ``start_hub``, ``end_hub`` and ``hub`` prefixes.

        Args:
            line: A single stripped line from the map file.

        Returns:
            A (prefix, Zone) tuple on success, or None when the line
            does not match the expected zone pattern.
        """
        match = re.match(_ZONE_PATTERN, line)
        if not match:
            return None

        zone_name = match.group(1)
        x_coord = int(match.group(2))
        y_coord = int(match.group(3))
        metadata = self._parse_metadata(match.group(4))

        # Build optional keyword arguments from the metadata block.
        optional_kwargs: dict[str, Any] = {}
        if metadata:
            optional_kwargs = {
                "zone_type": metadata.get("zone", "normal"),
                "color": metadata.get("color"),
                "max_drones": int(metadata.get("max_drones", 1)),
            }

        zone = Zone(name=zone_name, x=x_coord, y=y_coord, **optional_kwargs)
        prefix = line.split(":")[0]

        return prefix, zone

    def _build_connection(self, line: str) -> Connection | None:
        """
        Parses a connection line and constructs a Connection instance.

        The canonical connection name is the two zone names joined with
        a hyphen in alphabetical order, e.g. ``alpha-beta``.

        Args:
            line: A single stripped line from the map file.

        Returns:
            A Connection instance on success, or None when the line does
            not match the expected connection pattern.
        """
        match = re.match(_CONN_PATTERN, line)
        if not match:
            return None

        zone1 = match.group(1)
        zone2 = match.group(2)
        canonical_name = "-".join(sorted([zone1, zone2]))
        metadata = self._parse_metadata(match.group(3))

        optional_kwargs: dict[str, Any] = {}
        if metadata:
            optional_kwargs = {
                "max_link_capacity": int(
                    metadata.get("max_link_capacity", 1)
                )
            }

        return Connection(
            zone1=zone1,
            zone2=zone2,
            name=canonical_name,
            **optional_kwargs,
        )

    def parse(self, filepath: str) -> DroneMap:
        """
        Reads a map file and returns a fully validated DroneMap.

        Each line is classified by its prefix and dispatched to the
        appropriate builder. Zone and connection objects are collected
        into a dictionary before the final DroneMap is assembled.

        Args:
            filepath: Path to the plain-text map file to parse.

        Returns:
            A validated DroneMap instance ready for simulation.

        Raises:
            ValueError: When the file is missing a start or end zone.
            FileNotFoundError: When filepath does not exist.
        """
        d_map: dict[str, Any] = {
            "nb_drones": 0,
            "drones": {},
            "start_zone": None,
            "end_zone": None,
            "zones": {},
            "connections": {},
        }

        with open(filepath, "r") as map_file:
            for raw_line in map_file:
                line = raw_line.rstrip()

                # Skip blank lines and comments.
                if not line or line.startswith("#"):
                    continue

                # --- Fleet size declaration ---
                if line.startswith("nb_drones"):
                    fleet_size = int(line.split(":")[1].strip())
                    d_map["nb_drones"] = fleet_size

                    # Pre-populate the drone fleet with sequential IDs.
                    for drone_index in range(fleet_size):
                        drone_obj = Drone(drone_id=drone_index)
                        d_map["drones"][drone_index] = (drone_obj, 0)

                # --- Zone declarations ---
                elif ":" in line and not line.startswith("connection"):
                    result = self._build_zone(line)
                    if result is None:
                        continue

                    prefix, zone = result
                    zone_entry = (zone, 0)

                    # All hub types are registered in the zones dict.
                    d_map["zones"][zone.name] = zone_entry

                    if prefix == "start_hub":
                        d_map["start_zone"] = zone_entry
                    elif prefix == "end_hub":
                        d_map["end_zone"] = zone_entry

                # --- Connection declarations ---
                elif ":" in line and line.startswith("connection"):
                    connection = self._build_connection(line)
                    if connection is not None:
                        d_map["connections"][connection.name] = connection

        if d_map["start_zone"] is None:
            raise ValueError("Map file is missing a 'start_hub' declaration.")

        if d_map["end_zone"] is None:
            raise ValueError("Map file is missing an 'end_hub' declaration.")

        return DroneMap(
            nb_drones=d_map["nb_drones"],
            drones=d_map["drones"],
            start_zone=d_map["start_zone"],
            end_zone=d_map["end_zone"],
            zones=d_map["zones"],
            connections=d_map["connections"],
        )
