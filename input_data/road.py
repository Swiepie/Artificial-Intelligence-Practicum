from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Road:
    from_node: str
    to_node: str
    distance: float
    road_type: str
    speed: float

    @property
    def normal_travel_time(self) -> float:
        """Bereken de reistijd zonder congestie of verkeerscorrectie."""
        if self.speed <= 0:
            raise ValueError(f"Road speed must be positive: {self}")
        return self.distance / self.speed

class RoadStatus(str, Enum):
    OPEN = "Open"
    CONGESTED = "Congested"
    BLOCKED = "Blocked"


class RoadReportSource(str, Enum):
    CITIZEN = "Citizen"
    POLICE = "Police"
    SENSOR = "Sensor"


class Weather(str, Enum):
    CLEAR = "Clear"
    RAIN = "Rain"
    STORM = "Storm"


@dataclass(frozen=True, slots=True)
class RoadReport:
    from_node: str
    to_node: str
    weather: Weather
    source: RoadReportSource
    reported_status: RoadStatus


@dataclass(frozen=True, slots=True)
class RoadProbabilities:
    weather_prior: Mapping[Weather, float]
    road_status_given_weather: Mapping[Weather, Mapping[RoadStatus, float]]
    report_likelihood: Mapping[
        RoadReportSource, dict[RoadStatus, dict[RoadStatus, float]]
    ]

    def __post_init__(self) -> None:
        """Maak de prioriteitsverdeling alleen-lezen aan de buitenkant."""
        object.__setattr__(
            self, "weather_prior", MappingProxyType(dict(self.weather_prior))
        )
