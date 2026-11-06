from dataclasses import dataclass
from enum import Enum


class Availability(str, Enum):
    AVAILABLE = "Available"
    BUSY = "Busy"


class ResponderType(str, Enum):
    AMBULANCE = "Ambulance"
    POLICE_UNIT = "PoliceUnit"
    FIRE_TRUCK = "FireTruck"


@dataclass(frozen=True, slots=True)
class Responder:
    responder_id: str
    type: ResponderType
    start_location: str
    capabilities: frozenset[str]
    availability: Availability
    time_until_available: float

    def __post_init__(self) -> None:
        """Controleer beschikbaarheid en het bezit van minstens één vaardigheid."""
        if self.time_until_available < 0:
            raise ValueError("time_until_available cannot be negative")
        if not self.capabilities:
            raise ValueError(f"Responder {self.responder_id} has no capabilities")

    def can_handle(self, capability: str) -> bool:
        """Geef aan of deze responder de gevraagde vaardigheid bezit."""
        return capability in self.capabilities
