from dataclasses import dataclass
from enum import Enum


class IncidentPriority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    location: str
    priority: IncidentPriority
    deadline: float
    required_capability: str
    timestamp: float
    time_required: float

    def __post_init__(self) -> None:
        """Controleer de tijdsvoorwaarden van het incident."""
        if self.deadline < self.timestamp:
            raise ValueError(f"Incident {self.incident_id} deadline precedes its timestamp")
        if self.time_required < 0:
            raise ValueError("time_required cannot be negative")
