"""Niet-functionele en gevoeligheidsregressies op de echte simulatoruitvoer."""

import time

import pytest

from algorithms.bayesian_road import BayesianRoadEstimator
from algorithms.routing import RoadCostModel
from algorithms.simulation import Simulator


def test_simulator_is_byte_deterministisch(scenario2, tmp_path):
    """Draai Scenario2 tweemaal en vergelijk de bytes van plan en statistieken."""
    from algorithms.output import PlanWriter, StatisticsWriter

    outputs = []
    for index in range(2):
        directory = tmp_path / str(index)
        plan = directory / "plan.json"
        stats = directory / "statistics.txt"
        result = Simulator().run(scenario2)
        PlanWriter().write(plan, result, scenario2)
        StatisticsWriter().write_from_plan(stats, plan, scenario2)
        outputs.append((plan.read_bytes(), stats.read_bytes()))
    assert outputs[0] == outputs[1]


def test_scenario3_is_schaalbaar(scenario3):
    """Meet één volledige S3-simulatie en eis dat die binnen vijf seconden klaar is."""
    start = time.perf_counter()
    result = Simulator().run(scenario3)
    elapsed = time.perf_counter() - start
    assert result.assignments
    assert elapsed < 5.0


def test_prioriteit_wordt_eerst_gewogen():
    """Laat Critical en Low concurreren om één responder en verwacht Critical."""
    from algorithms.allocation import CspAllocator, ResponderState
    from algorithms.allocation import Assignment
    from algorithms.routing import RouteResult
    from input_data.incident import Incident, IncidentPriority
    from input_data.responder import Availability, Responder, ResponderType

    responder = Responder(
        "R1", ResponderType.AMBULANCE, "base", frozenset({"Rescue"}),
        Availability.AVAILABLE, 0,
    )
    state = ResponderState(responder, "base", 0)
    critical = Incident("critical", "critical", IncidentPriority.CRITICAL, 100, "Rescue", 0, 0)
    low = Incident("low", "low", IncidentPriority.LOW, 100, "Rescue", 0, 0)

    def route(start, goal):
        return RouteResult((start, goal), 1 if goal == "critical" else 2, True)

    assignments = CspAllocator().allocate((low, critical), (state,), route, 0)
    assert len(assignments) == 1
    assert assignments[0].incident.incident_id == "critical"


def test_gevoeligheidstabel_blokkeerstraf(scenario2):
    """Leg de echte scenario-gevoeligheid vast voor rapportage."""
    estimator = BayesianRoadEstimator(
        scenario2.road_probabilities, scenario2.road_reports
    )
    beliefs = estimator.estimate_all(scenario2.graph.roads)
    road = scenario2.graph.get_road("H1", "N3")
    costs = [
        RoadCostModel(scenario2.graph, beliefs, blocked_penalty=penalty).cost(road)
        for penalty in (0.0, 1000.0, 10000.0)
    ]
    blocked_probability = beliefs[("H1", "N3")].blocked_probability
    assert costs[1] - costs[0] == pytest.approx(1000 * blocked_probability)
    assert costs[2] - costs[0] == pytest.approx(10000 * blocked_probability)


def test_gevoeligheidstabel_bevat_alle_scenarios(scenario1, scenario2, scenario3):
    """Voer alle 3×2×2×2 modelvarianten uit en controleer de volledige tabel."""
    rows = []
    for name, scenario in (("S1", scenario1), ("S2", scenario2), ("S3", scenario3)):
        for traffic in (False, True):
            for penalty in (0.0, 10000.0):
                for map_status in (False, True):
                    result = Simulator().run(
                        scenario,
                        traffic_enabled=traffic,
                        blocked_penalty=penalty,
                        use_map_status=map_status,
                    )
                    rows.append((name, traffic, penalty, map_status, len(result.assignments)))
    assert len(rows) == 24
    assert {row[0] for row in rows} == {"S1", "S2", "S3"}
    assert len({row[4] for row in rows}) > 1


def test_scenario2_i2_wordt_niet_gegenereerd(generated_outputs):
    """I2 via N1->N2->N7 blijft door de blocked-drempel onbehandeld."""
    plan = generated_outputs["Scenario2"][1].read_text()
    assert '"incident_id": "I2"' not in plan
