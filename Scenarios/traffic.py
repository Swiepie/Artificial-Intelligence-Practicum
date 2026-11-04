from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class TrafficLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass(frozen=True, slots=True)
class TrafficObservation:
    observation_nr: int
    from_node: str
    to_node: str
    traffic: TrafficLevel


@dataclass(frozen=True, slots=True)
class TrafficProbabilities:
    initial: Mapping[TrafficLevel, float]
    transition: Mapping[TrafficLevel, Mapping[TrafficLevel, float]]
    emission: Mapping[TrafficLevel, Mapping[TrafficLevel, float]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial", MappingProxyType(dict(self.initial)))
