import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    latitude: float
    longitude: float
    location_type: str
    elevation: float


@dataclass(frozen=True)
class Road:
    source: str
    destination: str
    distance: float
    elevation_gain: float
    terrain: str
    accessible: bool
    blocked: bool


class CampusGraph:

    def __init__(self):
        self.locations: dict[str, Location] = {}
        self.adjacency: dict[str, list[Road]] = {}
        self.blocked_roads: set[tuple[str, str]] = set()

    @classmethod
    def from_json(
        cls,
        file_path: str | Path
    ) -> "CampusGraph":

        graph = cls()

        data = json.loads(
            Path(file_path).read_text(
                encoding="utf-8"
            )
        )

        for item in data["locations"]:
            location = Location(
                id=item["id"],
                name=item["name"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                location_type=item["type"],
                elevation=item.get("elevation", 0.0)
            )

            graph.add_location(location)

        for item in data["roads"]:
            if item["from"] not in graph.locations or item["to"] not in graph.locations:
                raise ValueError(
                    f"Invalid map road {item['from']} -> {item['to']}: "
                    "both endpoints must exist in locations."
                )
            source_location = graph.locations[item["from"]]
            destination_location = graph.locations[item["to"]]
            distance = float(item["distance"])
            straight_line_distance = graph.distance_between_points(
                source_location.latitude,
                source_location.longitude,
                destination_location.latitude,
                destination_location.longitude
            )
            if distance <= 0:
                raise ValueError(
                    f"Invalid map road {item['from']} -> {item['to']}: "
                    "distance must be greater than zero."
                )
            if distance + 1e-9 < straight_line_distance:
                raise ValueError(
                    f"Invalid map road {item['from']} -> {item['to']}: "
                    f"road distance {distance:.6f} km is shorter than "
                    f"straight-line distance {straight_line_distance:.6f} km."
                )
            expected_gain = max(
                0.0,
                destination_location.elevation - source_location.elevation
            )
            declared_gain = item.get("elevation_gain", expected_gain)
            if abs(float(declared_gain) - expected_gain) > 1e-9:
                raise ValueError(
                    f"Invalid map road {item['from']} -> {item['to']}: "
                    f"elevation_gain {declared_gain} does not match node "
                    f"elevations ({expected_gain})."
                )
            road = Road(
                source=item["from"],
                destination=item["to"],
                distance=distance,
                elevation_gain=max(0.0, declared_gain),
                terrain=item.get(
                    "terrain",
                    "paved"
                ),
                accessible=item.get(
                    "accessible",
                    True
                ),
                blocked=item.get(
                    "blocked",
                    False
                )
            )

            graph.add_road(road)

            if not item.get("one_way", False):
                reverse_road = Road(
                    source=road.destination,
                    destination=road.source,
                    distance=road.distance,
                    elevation_gain=max(
                        0.0,
                        source_location.elevation
                        - destination_location.elevation
                    ),
                    terrain=road.terrain,
                    accessible=road.accessible,
                    blocked=road.blocked
                )

                graph.add_road(reverse_road)

        return graph

    def add_location(
        self,
        location: Location
    ) -> None:

        self.locations[location.id] = location
        self.adjacency.setdefault(
            location.id,
            []
        )

    def add_road(
        self,
        road: Road
    ) -> None:

        if road.source not in self.locations:
            raise ValueError(
                f"Unknown source location: {road.source}"
            )

        if road.destination not in self.locations:
            raise ValueError(
                f"Unknown destination location: "
                f"{road.destination}"
            )

        self.adjacency[road.source].append(road)

    def block_road(
        self,
        source: str,
        destination: str
    ) -> None:

        self.blocked_roads.add(
            (source, destination)
        )

        if self._has_road(destination, source):
            self.blocked_roads.add(
                (destination, source)
            )

    def unblock_road(
        self,
        source: str,
        destination: str
    ) -> None:

        self.blocked_roads.discard(
            (source, destination)
        )

        if self._has_road(destination, source):
            self.blocked_roads.discard(
                (destination, source)
            )

    def _has_road(
        self,
        source: str,
        destination: str
    ) -> bool:
        return any(
            road.destination == destination
            for road in self.adjacency.get(source, [])
        )

    def get_neighbors(
        self,
        location_id: str,
        accessible_only: bool = False
    ) -> list[Road]:

        neighbours = []

        for road in self.adjacency.get(
            location_id,
            []
        ):
            road_key = (
                road.source,
                road.destination
            )

            if road.blocked:
                continue

            if road_key in self.blocked_roads:
                continue

            if (
                accessible_only
                and not road.accessible
            ):
                continue

            neighbours.append(road)

        return neighbours

    def find_location_by_name(
        self,
        name: str
    ) -> Location | None:

        search_name = name.strip().lower()

        for location in self.locations.values():
            if location.name.lower() == search_name:
                return location

        return None

    def nearest_location(
        self,
        latitude: float,
        longitude: float
    ) -> Location:

        return min(
            self.locations.values(),
            key=lambda location: self.distance_between_points(
                latitude,
                longitude,
                location.latitude,
                location.longitude
            )
        )

    def straight_line_distance(
        self,
        first_id: str,
        second_id: str
    ) -> float:

        first = self.locations[first_id]
        second = self.locations[second_id]

        return self.distance_between_points(
            first.latitude,
            first.longitude,
            second.latitude,
            second.longitude
        )

    @staticmethod
    def distance_between_points(
        first_latitude: float,
        first_longitude: float,
        second_latitude: float,
        second_longitude: float
    ) -> float:

        earth_radius_km = 6371.0

        latitude_difference = math.radians(
            second_latitude - first_latitude
        )

        longitude_difference = math.radians(
            second_longitude - first_longitude
        )

        first_latitude = math.radians(
            first_latitude
        )

        second_latitude = math.radians(
            second_latitude
        )

        value = (
            math.sin(latitude_difference / 2) ** 2
            + math.cos(first_latitude)
            * math.cos(second_latitude)
            * math.sin(longitude_difference / 2) ** 2
        )

        return earth_radius_km * 2 * math.atan2(
            math.sqrt(value),
            math.sqrt(1 - value)
        )
