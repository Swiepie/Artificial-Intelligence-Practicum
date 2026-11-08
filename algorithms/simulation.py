from dataclasses import dataclass
from typing import Iterable

from input_data.incident import Incident
from input_data.scenario_data import ScenarioData
from .allocation import Assignment, CspAllocator, ResponderState
from .routing import astar, build_road_cost_model


@dataclass(frozen=True, slots=True)
class SimulationResult:
    assignments: tuple[Assignment, ...]
    unassigned_incidents: tuple[Incident, ...]


class Simulator:
    """Plan opnieuw zodra nieuwe incidenten bekend worden."""

    def run(
        self,
        scenario: ScenarioData,
        *,
        traffic_enabled: bool = True,
        blocked_penalty: float = 10_000.0,
        use_map_status: bool = False,
    ) -> SimulationResult:
        """Voer de volledige tijdlijn uit zonder toekomstige incidenten te zien."""
        cost_model = build_road_cost_model(
            scenario,
            traffic_enabled=traffic_enabled,
            blocked_penalty=blocked_penalty,
            use_map_status=use_map_status,
        )
        states = {
            responder.responder_id: ResponderState(
                responder=responder,
                location=responder.start_location,
                available_at=responder.time_until_available,
            )
            for responder in scenario.responders
        }
        assigned: list[Assignment] = []
        assigned_ids: set[str] = set()
        for now in sorted({incident.timestamp for incident in scenario.incidents}):
            known = [
                incident
                for incident in scenario.incidents
                if incident.timestamp <= now and incident.incident_id not in assigned_ids
            ]
            planner = CspAllocator()
            batch = planner.allocate(
                known,
                states.values(),
                lambda start, goal: astar(
                    scenario.graph,
                    start,
                    goal,
                    cost_model.cost,
                    cost_model.travel_time,
                ),
                now,
            )
            for assignment in batch:
                assigned.append(assignment)
                assigned_ids.add(assignment.incident.incident_id)
                states[assignment.responder.responder_id] = ResponderState(
                    responder=assignment.responder,
                    location=assignment.incident.location,
                    available_at=assignment.completion_time,
                )
        return SimulationResult(
            assignments=tuple(assigned),
            unassigned_incidents=tuple(
                incident
                for incident in scenario.incidents
                if incident.incident_id not in assigned_ids
            ),
        )
