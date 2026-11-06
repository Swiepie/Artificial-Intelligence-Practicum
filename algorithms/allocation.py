from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

from input_data.incident import Incident, IncidentPriority
from input_data.responder import Responder
from .routing import RouteResult


@dataclass(frozen=True, slots=True)
class ResponderState:
    responder: Responder
    location: str
    available_at: float


@dataclass(frozen=True, slots=True)
class Assignment:
    incident: Incident
    responder: Responder
    route: RouteResult
    start_time: float
    arrival_time: float
    completion_time: float

    @property
    def response_time(self) -> float:
        """Geef de tijd tussen het bekend worden en de aankomst terug."""
        return self.arrival_time - self.incident.timestamp


RouteFinder = Callable[[str, str], RouteResult]


class GreedyAllocator:
    """Basisstrategie die per incident de snelste haalbare responder kiest."""

    def allocate(
        self,
        incidents: Iterable[Incident],
        states: Iterable[ResponderState],
        route_finder: RouteFinder,
        now: float,
    ) -> tuple[Assignment, ...]:
        """Wijs incidenten op volgorde van prioriteit hebberig toe."""
        available = list(states)
        assignments: list[Assignment] = []
        for incident in sorted(incidents, key=self._incident_order):
            candidates = self._candidates(incident, available, route_finder, now)
            if not candidates:
                continue
            assignment = min(candidates, key=lambda item: item.arrival_time)
            assignments.append(assignment)
            available.remove(next(state for state in available
                                  if state.responder.responder_id == assignment.responder.responder_id))
        return tuple(assignments)

    @staticmethod
    def _incident_order(incident: Incident) -> tuple[int, float, str]:
        """Bepaal de sorteervolgorde: prioriteit, deadline en identifier."""
        weights = {
            IncidentPriority.CRITICAL: 0,
            IncidentPriority.HIGH: 1,
            IncidentPriority.MEDIUM: 2,
            IncidentPriority.LOW: 3,
        }
        return weights[incident.priority], incident.deadline, incident.incident_id

    @staticmethod
    def _candidates(
        incident: Incident,
        states: Iterable[ResponderState],
        route_finder: RouteFinder,
        now: float,
    ) -> list[Assignment]:
        """Bouw alle haalbare responder-incidentcombinaties op."""
        candidates = []
        for state in states:
            if not state.responder.can_handle(incident.required_capability):
                continue
            route = route_finder(state.location, incident.location)
            if not route.reachable:
                continue
            start = max(now, incident.timestamp, state.available_at)
            arrival = start + (route.travel_time or route.cost)
            if arrival <= incident.deadline:
                candidates.append(
                    Assignment(
                        incident=incident,
                        responder=state.responder,
                        route=route,
                        start_time=start,
                        arrival_time=arrival,
                        completion_time=arrival + incident.time_required,
                    )
                )
        return candidates


class CspAllocator:
    """Exacte batch-CSP met backtracking en branch-and-bound."""

    def allocate(
        self,
        incidents: Iterable[Incident],
        states: Iterable[ResponderState],
        route_finder: RouteFinder,
        now: float,
    ) -> tuple[Assignment, ...]:
        """Zoek de beste gezamenlijke toewijzing voor de huidige batch."""
        incidents = tuple(sorted(incidents, key=GreedyAllocator._incident_order))
        states = tuple(states)
        options = {
            incident.incident_id: GreedyAllocator._candidates(
                incident, states, route_finder, now
            )
            for incident in incidents
        }
        best_cost = float("inf")
        best: tuple[Assignment, ...] = ()
        priority_weight = {
            IncidentPriority.CRITICAL: 1000.0,
            IncidentPriority.HIGH: 100.0,
            IncidentPriority.MEDIUM: 10.0,
            IncidentPriority.LOW: 1.0,
        }

        def search(
            index: int,
            used: set[str],
            selected: list[Assignment],
            cost: float,
        ) -> None:
            """Doorloop recursief alle haalbare keuzes en houd de beste bij."""
            nonlocal best_cost, best
            if cost >= best_cost:
                return
            if index == len(incidents):
                best_cost = cost
                best = tuple(selected)
                return
            incident = incidents[index]
            search(index + 1, used, selected, cost + priority_weight[incident.priority] * 10000)
            for candidate in options[incident.incident_id]:
                responder_id = candidate.responder.responder_id
                if responder_id in used:
                    continue
                selected.append(candidate)
                used.add(responder_id)
                search(
                    index + 1,
                    used,
                    selected,
                    cost + priority_weight[incident.priority] * candidate.response_time,
                )
                used.remove(responder_id)
                selected.pop()

        search(0, set(), [], 0.0)
        return tuple(sorted(best, key=lambda item: item.incident.incident_id))
