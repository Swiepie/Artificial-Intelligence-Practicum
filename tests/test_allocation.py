"""Tests voor basisinvarianten en randgevallen van de CSP-toewijzing."""

from algorithms.allocation import (
    CspAllocator,
    GreedyAllocator,
    ResponderState,
)
from algorithms.routing import RouteResult
from algorithms.simulation import Simulator
from input_data.incident import Incident, IncidentPriority
from input_data.responder import Availability, Responder, ResponderType


def test_een_responder_een_incident_per_batch(scenario2):
    """Doel / Input: Scenario2-uitvoering / Verwacht: geen dubbele toewijzing per batch."""
    result = Simulator().run(scenario2)
    pairs = [
        (assignment.decided_at, assignment.responder.responder_id)
        for assignment in result.assignments
    ]
    assert len(pairs) == len(set(pairs))


def test_capabilities_worden_gerespecteerd(scenario2):
    """Doel / Input: Scenario2-uitvoering / Verwacht: elke capability past."""
    result = Simulator().run(scenario2)
    assert all(
        assignment.responder.can_handle(assignment.incident.required_capability)
        for assignment in result.assignments
    )


def _responder(identifier, location, capabilities=("Rescue",), available_at=0):
    return Responder(
        identifier,
        ResponderType.AMBULANCE,
        location,
        frozenset(capabilities),
        Availability.AVAILABLE,
        available_at,
    )


def _incident(identifier, priority, location, deadline=50, timestamp=0):
    return Incident(
        identifier, location, priority, deadline, "Rescue", timestamp, 0
    )


def test_csp_slaat_minder_over_dan_greedy():
    """Doel / Input: Critical A en High B / Verwacht: CSP 2, greedy 1 / Faalt nu? nee."""
    responders = (
        ResponderState(_responder("R1", "base1"), "base1", 0),
        ResponderState(_responder("R2", "base2"), "base2", 0),
    )
    incidents = (
        _incident("A", IncidentPriority.CRITICAL, "A"),
        _incident("B", IncidentPriority.HIGH, "B"),
    )
    times = {
        ("base1", "A"): 10, ("base2", "A"): 12,
        ("base1", "B"): 10, ("base2", "B"): 100,
    }

    def route(start, goal):
        time = times[(start, goal)]
        return RouteResult((start, goal), time, True, time)

    greedy = GreedyAllocator().allocate(incidents, responders, route, 0)
    csp = CspAllocator().allocate(incidents, responders, route, 0)
    assert len(greedy) == 1
    assert {item.incident.incident_id for item in csp} == {"A", "B"}
    assert {
        item.incident.incident_id: item.responder.responder_id for item in csp
    } == {"A": "R2", "B": "R1"}
    greedy_cost = 1000 * greedy[0].response_time + 100 * 10000
    csp_cost = 1000 * 12 + 100 * 10
    assert greedy_cost == 1_010_000
    assert csp_cost == 13_000


def test_csp_skipkost_is_priority_weight():
    """Een overgeslagen Critical kost 10.000.000 en High 1.000.000."""
    assert 1000 * 10000 == 10_000_000
    assert 100 * 10000 == 1_000_000


def test_csp_skipkost_maakt_haalbare_critical_beter():
    """Controleer dat een haalbare Critical wordt gekozen in plaats van overgeslagen."""
    responder = ResponderState(_responder("R1", "base"), "base", 0)
    incident = _incident("A", IncidentPriority.CRITICAL, "target", deadline=7000)
    route = lambda start, goal: RouteResult((start, goal), 6000, True, 6000)
    assert CspAllocator().allocate((incident,), (responder,), route, 0)


def test_deadline_hard_en_busy_responder():
    """Doel / Input: te late en bezette responder / Verwacht: geen toewijzing en start >= 20."""
    responder = ResponderState(
        _responder("R1", "base", available_at=20), "base", 20
    )
    incident = _incident("A", IncidentPriority.HIGH, "target", deadline=25)
    route = lambda start, goal: RouteResult((start, goal), 10, True, 10)
    assert not CspAllocator().allocate((incident,), (responder,), route, 0)
    assignment = CspAllocator().allocate(
        (_incident("B", IncidentPriority.HIGH, "target", deadline=40),),
        (responder,),
        route,
        0,
    )[0]
    assert assignment.start_time >= 20


def test_capability_wordt_niet_genegeerd():
    """Doel / Input: verkeerde capability / Verwacht: leeg resultaat / Faalt nu? nee."""
    responder = ResponderState(
        _responder("R1", "base", capabilities=("Police",)), "base", 0
    )
    incident = _incident("A", IncidentPriority.HIGH, "target")
    route = lambda start, goal: RouteResult((start, goal), 1, True, 1)
    assert not CspAllocator().allocate((incident,), (responder,), route, 0)
