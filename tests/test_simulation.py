"""Tests voor tijdcausaliteit in de simulatie."""

from algorithms.simulation import Simulator
from dataclasses import replace


def test_toewijzingen_krijgen_beslismoment(scenario2):
    """Doel / Input: Scenario2 / Verwacht: decided_at <= start_time."""
    result = Simulator().run(scenario2)
    assert all(
        assignment.decided_at <= assignment.start_time
        for assignment in result.assignments
    )


def test_geen_start_voor_bekend_en_geen_overlap(scenario2):
    """Doel / Input: Scenario2 / Verwacht: causaliteit en geen overlap / Faalt nu? nee."""
    result = Simulator().run(scenario2)
    assert all(
        assignment.start_time >= assignment.incident.timestamp
        for assignment in result.assignments
    )
    for responder_id in {
        item.responder.responder_id for item in result.assignments
    }:
        assignments = sorted(
            (
                item for item in result.assignments
                if item.responder.responder_id == responder_id
            ),
            key=lambda item: item.start_time,
        )
        assert all(
            current.start_time >= previous.completion_time
            for previous, current in zip(assignments, assignments[1:])
        )


def test_geen_toekomst_zien(scenario2):
    """Doel / Input: prefix tot T / Verwacht: beslissingen blijven gelijk / Faalt nu? nee."""
    result = Simulator().run(scenario2)
    timestamps = sorted({incident.timestamp for incident in scenario2.incidents})
    cutoff = timestamps[len(timestamps) // 2]
    prefix = {
        item.incident.incident_id: (
            item.responder.responder_id, item.start_time, item.decided_at
        )
        for item in result.assignments
        if item.decided_at <= cutoff
    }
    truncated = replace(
        scenario2,
        incidents=tuple(
            incident for incident in scenario2.incidents
            if incident.timestamp <= cutoff
        ),
    )
    truncated_result = Simulator().run(truncated)
    truncated_prefix = {
        item.incident.incident_id: (
            item.responder.responder_id, item.start_time, item.decided_at
        )
        for item in truncated_result.assignments
    }
    assert truncated_prefix == prefix
