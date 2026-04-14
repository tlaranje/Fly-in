from src.Parsing.validators import DroneMap, Zone, Connection
from src.Simulation import Drone
from typing import Any
import re


class MapParser:
    def parse_metadata(self, data: str) -> dict[str, Any]:
        if data is None:
            return {}
        temp_data: list[str] = data.split(' ')
        metadata: dict[str, Any] = {}
        for d in temp_data:
            if d.endswith("rainbow"):
                metadata[d.split('=')[0]] = "green"
            elif '=' in d:
                metadata[d.split('=')[0]] = d.split('=')[1]

        return metadata

    def parse(self, filepath: str) -> DroneMap:
        map_data: dict[str, Any] = {
            "nb_drones": 0,
            "drones": {},
            "start_zone": None,
            "end_zone": None,
            "zones": {},
            "connections": {},
        }

        with open(filepath, "r") as fd:
            for line in fd:
                line = line.rstrip()

                if line.startswith('#'):
                    continue

                if line.startswith("nb_drones"):
                    map_data["nb_drones"] = int(line.split(':')[1].strip())
                    for i in range(map_data["nb_drones"]):
                        map_data["drones"][i + 1] = Drone(drone_id=i + 1)

                if ":" in line and not line.startswith("connection"):
                    ZONE_PATTERN = re.compile(r"""
                        ^\w+:             # line starts with zone type prefix
                        \s+(\S+)\s+       # whitespace + zone name + whitespace
                        (-?\d+)\s+(-?\d+) # x + whitespace + y
                        (?:               # optional metadata block
                            \s+\[         # whitespace + opening bracket
                            ([^\]]*)\]    # metadata content + closing bracket
                        )?
                    """, re.VERBOSE)

                    match = re.match(ZONE_PATTERN, line)

                    if match:
                        name = match.group(1)
                        x = int(match.group(2))
                        y = int(match.group(3))
                        meta = self.parse_metadata(match.group(4))

                        zone = Zone(
                            name=name, x=x, y=y,
                            **({} if not meta else {
                                'zone_type': meta.get('zone', 'normal'),
                                'color': meta.get('color'),
                                'max_drones': int(meta.get('max_drones', 1)),
                            })
                        )

                        prefix = line.split(':')[0]
                        if prefix == "start_hub":
                            map_data["zones"][zone.name] = zone
                            map_data["start_zone"] = zone
                        elif prefix == "end_hub":
                            map_data["zones"][zone.name] = zone
                            map_data["end_zone"] = zone
                        elif prefix == "hub":
                            map_data["zones"][zone.name] = zone
                if ":" in line and line.startswith("connection"):
                    CONN_PATTERN = re.compile(r"""
                        ^connection:    # line starts with connection:
                        \s+([^-\s]+)-   # whitespace + zone1 name + separator
                        ([^-\s]+)       # zone2 name
                        (?:             # optional metadata block
                            \s+\[       # whitespace + opening bracket
                            ([^\]]*)\]  # metadata content + closing bracket
                        )?
                    """, re.VERBOSE)
                    match = re.match(CONN_PATTERN, line)

                    if match:
                        zone1 = match.group(1)
                        zone2 = match.group(2)
                        name = "-".join(sorted([zone1, zone2]))
                        meta = self.parse_metadata(match.group(3))
                        c = Connection(
                            zone1=zone1, zone2=zone2, name=name,
                            **({} if not meta else {
                                    'max_link_capacity': int(meta.get(
                                        'max_link_capacity', 1
                                    ))
                            })
                        )
                        map_data["connections"][c.name] = c

        if map_data["start_zone"] is None:
            raise ValueError("Missing start_zone")

        if map_data["end_zone"] is None:
            raise ValueError("Missing end_zone")

        return DroneMap(
            nb_drones=map_data["nb_drones"],
            drones=map_data["drones"],
            start_zone=map_data["start_zone"],
            end_zone=map_data["end_zone"],
            zones=map_data["zones"],
            connections=map_data["connections"]
        )
