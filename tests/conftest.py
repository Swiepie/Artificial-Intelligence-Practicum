"""Gedeelde fixtures voor de regressietests."""

from pathlib import Path

import pytest

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
