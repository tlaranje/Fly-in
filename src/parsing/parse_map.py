from typing import Any
import re
from src.core import DroneMap, Zone, Connection, Drone

# Matches a zone line: <prefix>: <name> <x> <y> [metadata]
_ZONE_PATTERN = re.compile(r"""
    ^\w+:              # prefixo
    \s+([^-\s]+)\s+    # nome (NÃO permite hífens)
    (-?\d+)\s+(-?\d+)  # coordenadas x e y
    (?:\s+(.*))?       # metadados opcionais
""", re.VERBOSE)

# Matches a connection line: connection: <z1>-<z2> [metadata]
_CONN_PATTERN = re.compile(r"""
    ^connection:
    \s+([^-\s]+)       # zona 1
    -                  # separador
    ([^-\s]+)          # zona 2
    (?:\s+(.*))?       # metadados opcionais
""", re.VERBOSE)


class MapParser:
    """
    Parses a plain-text map file into a validated DroneMap instance.
    Version 2.3: Explicit presence check for metadata defaults.
    """

    def _parse_metadata(self, raw_metadata: str | None) -> dict[str, Any]:
        """Parses [key=value] pairs into a dictionary correctly."""
        if not raw_metadata:
            return {}

        parsed: dict[str, Any] = {}
        clean_text = raw_metadata.strip().replace("[", "").replace("]", "")
        tokens = clean_text.split()

        for token in tokens:
            if "=" not in token:
                raise ValueError(
                    f"Map Error: Malformed metadata token '{token}'. "
                    "Expected 'key=value'."
                )

            key, _, value = token.partition("=")
            k, v = key.strip(), value.strip()

            if not k or not v:
                raise ValueError(f"Map Error: Invalid metadata pair '{token}'")

            parsed[k] = v

        return parsed

    def _build_zone(self, line: str) -> tuple[str, Zone] | None:
        """Parses a hub line and constructs a Zone instance."""
        match = re.match(_ZONE_PATTERN, line)
        if not match:
            parts = line.split(":")
            prefix = parts[0].strip()
            if prefix in ["start_hub", "end_hub", "hub"]:
                content_parts = parts[1].strip().split()
                if content_parts and "-" in content_parts[0]:
                    raise ValueError(
                        f"Map Error: Zone name '{content_parts[0]}' "
                        "can not have '-' in the name."
                    )
                raise ValueError(f"Map Error: Invalid zone format: '{line}'")
            return None

        zone_name = match.group(1)
        x_coord, y_coord = int(match.group(2)), int(match.group(3))

        remaining = match.group(4)
        raw_metadata = None
        if remaining:
            remaining = remaining.strip()
            if remaining.startswith("[") and remaining.endswith("]"):
                raw_metadata = remaining[1:-1]
            else:
                raise ValueError(
                    f"Map Error: Invalid metadata format in zone '{zone_name}'"
                )

        metadata = self._parse_metadata(raw_metadata)

        # Lógica de verificação explícita para max_drones
        if "max_drones" not in metadata:
            max_dr = 1
        else:
            try:
                max_dr = int(metadata["max_drones"])
            except ValueError:
                raise ValueError(
                    f"Map Error: max_drones in '{zone_name}' must be int."
                )

        if max_dr < 1:
            raise ValueError(
                f"Map Error: Zone '{zone_name}' capacity must be at least 1."
            )

        zone = Zone(
            name=zone_name, x=x_coord, y=y_coord,
            zone_type=metadata.get("zone", "normal"),
            color=metadata.get("color"),
            max_drones=max_dr
        )
        return line.split(":")[0], zone

    def _build_connection(
        self, line: str, zones: dict[str, Any]
    ) -> Connection | None:
        """Parses connection: Z1-Z2."""
        match = re.match(_CONN_PATTERN, line)
        if not match:
            content = line.replace("connection:", "").strip().split()[0]
            if content.count("-") > 1:
                raise ValueError(
                    f"Map Error: Connection '{content}' has too many hífens."
                )
            raise ValueError(f"Map Error: Invalid connection format: '{line}'")

        z1, z2 = match.group(1), match.group(2)
        missing = [z for z in [z1, z2] if z not in zones]
        if missing:
            raise ValueError(
                f"Map Error: Undefined zone(s) in connection: {missing}"
            )

        metadata = self._parse_metadata(match.group(3))
        val_from_map = metadata.get("max_link_capacity")
        if val_from_map is None:
            max_l = 1
        else:
            try:
                max_l = int(val_from_map)
            except ValueError:
                raise ValueError(
                    f"Map Error: max_link_capacity in '{z1}-{z2}' must be int."
                )

        if max_l < 1:
            raise ValueError(
                f"Map Error: Connection '{z1}-{z2}' capacity must be >= 1."
            )

        return Connection(
            zone1=z1, zone2=z2,
            name="-".join(sorted([z1, z2])),
            max_link_capacity=max_l
        )

    def parse(self, filepath: str) -> DroneMap:
        """Main entry point for parsing the map file."""
        dmap: dict[str, Any] = {
            "nb_drones": None, "drones": {}, "zones": {}, "connections": {},
            "start_zone": None, "end_zone": None
        }
        raw_conns: list[str] = []
        seen_coords: dict[tuple[float, float], str] = {}

        with open(filepath, "r") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("nb_drones:"):
                    count_str = line.split(":")[1].strip()
                    try:
                        count = int(count_str)
                    except ValueError:
                        raise ValueError(
                            f"Map Error: '{count_str}' is not int"
                        )

                    if count < 1:
                        raise ValueError("Map Error: nb_drones must be >= 1.")
                    dmap["nb_drones"] = count
                    dmap["drones"] = {
                        i: (Drone(drone_id=i), 0) for i in range(count)
                    }
                elif line.startswith("connection:"):
                    raw_conns.append(line)
                elif ":" in line:
                    res = self._build_zone(line)
                    if res:
                        prefix, zone = res
                        if (zone.x, zone.y) in seen_coords:
                            existing_zone_name = seen_coords[(zone.x, zone.y)]
                            raise ValueError(
                                f"Map Error: Zones ['{existing_zone_name}', "
                                f"'{zone.name}'] share the same coordinates "
                                f"{(zone.x, zone.y)}."
                            )

                        if zone.name in dmap["zones"]:
                            raise ValueError(
                                f"Map Error: Duplicate name detected. "
                                f"Multiple zones share the name '{zone.name}'."
                            )

                        seen_coords[(zone.x, zone.y)] = zone.name
                        dmap["zones"][zone.name] = (zone, 0)

                        if prefix == "start_hub":
                            dmap["start_zone"] = (zone, 0)
                        elif prefix == "end_hub":
                            dmap["end_zone"] = (zone, 0)

        if not all([dmap["nb_drones"], dmap["start_zone"], dmap["end_zone"]]):
            raise ValueError("Map Error: Incomplete map definitions.")

        for cl in raw_conns:
            conn = self._build_connection(cl, dmap["zones"])
            if conn:
                if conn.name in dmap["connections"]:
                    raise ValueError(f"Duplicate connection: {conn.name}")
                dmap["connections"][conn.name] = conn

        return DroneMap(
            nb_drones=dmap["nb_drones"], drones=dmap["drones"],
            start_zone=dmap["start_zone"], end_zone=dmap["end_zone"],
            zones=dmap["zones"], connections=dmap["connections"]
        )
