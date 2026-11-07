"""Tests voor het formaat van statistics.txt."""

from pathlib import Path

from algorithms.output import StatisticsWriter
from algorithms.simulation import Simulator
from input_data.scenario_loader import ScenarioLoader


def test_gegenereerde_statistieken_hebben_verplicht_formaat():
    """Doel / Input: drie scenario-uitvoeren / Verwacht: seconden en decimalen."""
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        text = (Path("Scenarios") / name / "statistics.txt").read_text()
        assert "* Average response time: " in text
        assert " s" in text
        assert "* Deadlines met: " in text


def test_statistieken_herberekend_uit_plan(tmp_path):
    """Doel / Input: S1-planbestand / Verwacht: writer accepteert alleen plan-invoer."""
    scenario_dir = Path("Scenarios/Scenario1")
    scenario = ScenarioLoader().load(scenario_dir)
    result = Simulator().run(scenario)
    plan_path = tmp_path / "plan.json"
    stats_path = tmp_path / "statistics.txt"
    from algorithms.output import PlanWriter

    PlanWriter().write(plan_path, result, scenario)
    StatisticsWriter().write_from_plan(stats_path, plan_path, scenario)
    assert "* 4 incidents handled" in stats_path.read_text()
