from dataclasses import dataclass
from typing import Iterable

from input_data.city_graph import CityGraph
from input_data.incident import Incident
from input_data.responder import Responder
from .allocation import Assignment


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str


class PlanValidator:
    """Controleer operationele voorwaarden van een gegenereerd plan."""

    def validate(
        self,
        assignments: Iterable[Assignment],
        graph: CityGraph,
        responders: Iterable[Responder],
        incidents: Iterable[Incident],
    ) -> tuple[ValidationIssue, ...]:
        """Geef alle gevonden validatiefouten terug zonder vroegtijdig te stoppen."""
        responder_map = {responder.responder_id: responder for responder in responders}
        incident_map = {incident.incident_id: incident for incident in incidents}
        issues: list[ValidationIssue] = []
        seen_incidents: set[str] = set()
        schedules: dict[str, list[Assignment]] = {}
        for assignment in assignments:
            incident = assignment.incident
            responder = responder_map.get(assignment.responder.responder_id)
            if responder is None:
                issues.append(ValidationIssue("unknown_responder", assignment.responder.responder_id))
                continue
            if incident.incident_id in seen_incidents:
                issues.append(ValidationIssue("duplicate_incident", incident.incident_id))
            seen_incidents.add(incident.incident_id)
            if incident.incident_id not in incident_map:
                issues.append(ValidationIssue("unknown_incident", incident.incident_id))
            if not responder.can_handle(incident.required_capability):
                issues.append(ValidationIssue("capability", incident.incident_id))
            if assignment.start_time < incident.timestamp:
                issues.append(ValidationIssue("starts_before_known", incident.incident_id))
            if assignment.start_time < responder.time_until_available:
                issues.append(ValidationIssue("responder_unavailable", incident.incident_id))
            if assignment.arrival_time > incident.deadline:
                issues.append(ValidationIssue("missed_deadline", incident.incident_id))
            if not assignment.route.reachable or not assignment.route.path:
                issues.append(ValidationIssue("unreachable", incident.incident_id))
            elif assignment.route.path[-1] != incident.location:
                issues.append(ValidationIssue("wrong_destination", incident.incident_id))
            for first, second in zip(assignment.route.path, assignment.route.path[1:]):
                try:
                    graph.get_road(first, second)
                except KeyError:
                    issues.append(ValidationIssue("invalid_path", f"{first}->{second}"))
            schedules.setdefault(responder.responder_id, []).append(assignment)
        for responder_id, assignments_for_responder in schedules.items():
            ordered = sorted(assignments_for_responder, key=lambda item: item.start_time)
            responder = responder_map[responder_id]
            expected_location = responder.start_location
            expected_available_at = responder.time_until_available
            for assignment in ordered:
                if assignment.start_time < expected_available_at:
                    issues.append(
                        ValidationIssue("responder_unavailable", assignment.incident.incident_id)
                    )
                if not assignment.route.path or assignment.route.path[0] != expected_location:
                    issues.append(
                        ValidationIssue(
                            "wrong_origin",
                            f"{responder_id} expected {expected_location}",
                        )
                    )
                expected_location = assignment.incident.location
                expected_available_at = assignment.completion_time
            for previous, current in zip(ordered, ordered[1:]):
                if current.start_time < previous.completion_time:
                    issues.append(ValidationIssue("overlap", responder_id))
        return tuple(issues)
