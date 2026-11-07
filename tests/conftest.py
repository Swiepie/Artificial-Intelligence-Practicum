"""Gedeelde fixtures voor de regressietests."""

from pathlib import Path

import pytest

from algorithms.output import PlanWriter, StatisticsWriter
from algorithms.simulation import Simulator
from input_data.scenario_loader import ScenarioLoader


@pytest.fixture(scope="session")
def scenario1():
    """Laad Scenario1 voor algemene regressietests."""
    root = Path(__file__).parents[1]
    return ScenarioLoader().load(root / "Scenarios" / "Scenario1")


@pytest.fixture(scope="session")
def scenario2():
    """Laad Scenario2 voor de Bayes- en kostmodeltests."""
    root = Path(__file__).parents[1]
    return ScenarioLoader().load(root / "Scenarios" / "Scenario2")


@pytest.fixture(scope="session")
def scenario3():
    """Laad Scenario3 voor de verkeersfactorgrens."""
    root = Path(__file__).parents[1]
    return ScenarioLoader().load(root / "Scenarios" / "Scenario3")


@pytest.fixture(scope="session")
def generated_outputs(tmp_path_factory):
    """Draai iedere simulatorregressie opnieuw en schrijf naar een tijdelijke map."""
    root = Path(__file__).parents[1]
    outputs = {}
    tmp_path = tmp_path_factory.mktemp("generated_outputs")
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        scenario = ScenarioLoader().load(root / "Scenarios" / name)
        result = Simulator().run(scenario)
        directory = tmp_path / name
        plan_path = directory / "plan.json"
        stats_path = directory / "statistics.txt"
        PlanWriter().write(plan_path, result, scenario)
        StatisticsWriter().write_from_plan(stats_path, plan_path, scenario)
        outputs[name] = (scenario, plan_path, stats_path)
    return outputs
