"""Tests voor het formaat van statistics.txt."""

from algorithms.output import StatisticsWriter
from algorithms.simulation import Simulator
from input_data.city_graph import CityGraph, Node
from input_data.incident import Incident, IncidentPriority
from input_data.scenario_data import ScenarioData
from input_data.responder import Availability, Responder, ResponderType


def test_gegenereerde_statistieken_hebben_verplicht_formaat(generated_outputs):
    """Doel / Input: drie scenario-uitvoeren / Verwacht: seconden en decimalen."""
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        text = generated_outputs[name][2].read_text()
        assert "* Average response time: " in text
        assert " s" in text
        assert "* Deadlines met: " in text


def test_statistieken_herberekend_uit_plan(tmp_path, scenario1):
    """Doel / Input: S1-planbestand / Verwacht: writer accepteert alleen plan-invoer."""
    scenario = scenario1
    result = Simulator().run(scenario)
    plan_path = tmp_path / "plan.json"
    stats_path = tmp_path / "statistics.txt"
    direct_stats_path = tmp_path / "direct-statistics.txt"
    from algorithms.output import PlanWriter

    PlanWriter().write(plan_path, result, scenario)
    StatisticsWriter().write_from_plan(stats_path, plan_path, scenario)
    StatisticsWriter().write(direct_stats_path, result, scenario)
    text = stats_path.read_text()
    assert f"* {len(result.assignments)} incidents handled" in text
    assert "* Average response time: " in text
    assert "* Deadlines met: " in text
    assert text == direct_stats_path.read_text()


def test_statistieken_microscenario(scenario1, tmp_path):
    """Controleer met één aankomst en één gemist incident 40,0 s en 50,0%."""
    scenario = ScenarioData(
        graph=CityGraph(
            nodes={"A": Node("A", "A", 0, 0, "normal")},
            roads=(),
        ),
        responders=(
            Responder("R1", ResponderType.AMBULANCE, "A", frozenset({"Rescue"}),
                      Availability.AVAILABLE, 0),
        ),
        incidents=(
            Incident("I1", "A", IncidentPriority.HIGH, 100, "Rescue", 0, 0),
            Incident("I2", "A", IncidentPriority.LOW, 10, "Rescue", 0, 0),
        ),
        road_reports=(),
        traffic_observations=(),
        road_probabilities=scenario1.road_probabilities,
        traffic_probabilities=scenario1.traffic_probabilities,
    )
    import json

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps([
        {"responder_id": "R1", "incident_id": "I1", "path": ["A"], "time": 40}
    ]))
    stats_path = tmp_path / "statistics.txt"
    StatisticsWriter().write_from_plan(stats_path, plan_path, scenario)
    text = stats_path.read_text()
    assert "* Average response time: 40.0 s" in text
    assert "* Deadlines met: 50.0%" in text
