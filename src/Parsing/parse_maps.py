from src.Parsing.validators import DroneMap, Zone, Connection
from typing import Any
import re


class MapParser:
    def __init__(self, filepath: str):
        self.filepath = filepath

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

    def parse(self) -> DroneMap:
        map_data: dict[str, Any] = {
            "nb_drones": "",
            "start_hub": Zone,
            "end_hub": Zone,
            "hubs": [],
            "connections": [],
        }

        with open(self.filepath, "r") as fd:
            for line in fd:
                line = line.rstrip()

                if line.startswith('#'):
                    continue
                if line.startswith("nb_drones"):
                    map_data["nb_drones"] = int(line.split(':')[1].strip())
                if "hub" in line:
                    pattern = re.compile(r"""
                        ^\w+:             # line starts with zone type prefix
                        \s+(\S+)\s+       # whitespace + zone name + whitespace
                        (-?\d+)\s+(-?\d+) # x + whitespace + y
                        (?:               # optional metadata block
                            \s+\[         # whitespace + opening bracket
                            ([^\]]*)\]    # metadata content + closing bracket
                        )?
                    """, re.VERBOSE)

                    match = re.match(pattern, line)

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
                            map_data["start_hub"] = zone
                        elif prefix == "end_hub":
                            map_data["end_hub"] = zone
                        elif prefix == "hub":
                            map_data["hubs"].append(zone)
                if line.startswith("connection"):
                    pattern = re.compile(r"""
                        ^connection:    # line starts with connection:
                        \s+([^-\s]+)-   # whitespace + zone1 name + separator
                        ([^-\s]+)       # zone2 name
                        (?:             # optional metadata block
                            \s+\[       # whitespace + opening bracket
                            ([^\]]*)\]  # metadata content + closing bracket
                        )?
                    """, re.VERBOSE)
                    match = re.match(pattern, line)

                    if match:
                        zone1 = match.group(1)
                        zone2 = match.group(2)
                        meta = self.parse_metadata(match.group(3))
                    c = Connection(
                        zone1=zone1, zone2=zone2,
                        **({} if not meta else {
                                'max_link_capacity': int(meta.get(
                                    'max_link_capacity', 1
                                ))
                        })
                    )
                    map_data["connections"].append(c)

        return DroneMap(
            nb_drones=map_data["nb_drones"],
            start_hub=map_data["start_hub"],
            end_hub=map_data["end_hub"],
            hubs=map_data["hubs"],
            connections=map_data["connections"]
        )
