from dataclasses import dataclass

from .city_graph import CityGraph
from .incident import Incident
from .responder import Responder
from .road import RoadProbabilities, RoadReport
from .traffic import TrafficObservation, TrafficProbabilities


@dataclass(frozen=True, slots=True)
class ScenarioData:
    graph: CityGraph
    responders: tuple[Responder, ...]
    incidents: tuple[Incident, ...]
    road_reports: tuple[RoadReport, ...]
    traffic_observations: tuple[TrafficObservation, ...]
    road_probabilities: RoadProbabilities
    traffic_probabilities: TrafficProbabilities

    def incidents_at(self, timestamp: float) -> tuple[Incident, ...]:
        """Geef incidenten terug die exact op dit tijdstip bekend worden."""
        return tuple(
            incident
            for incident in self.incidents
            if incident.timestamp == timestamp
        )

    def pending_incidents(self, timestamp: float) -> tuple[Incident, ...]:
        """Geef alle incidenten terug die uiterlijk nu bekend zijn."""
        return tuple(
            incident
            for incident in self.incidents
            if incident.timestamp <= timestamp
        )
