"""Regressiecontrole voor de gegenereerde scenario-uitvoer."""

import json
from pathlib import Path


def test_scenario_plannen_zijn_deterministisch_vormgegeven(generated_outputs):
    """Doel / Input: plan.json van S1-S3 / Verwacht: lijst met vaste sleutels."""
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        plan = json.loads(generated_outputs[name][1].read_text())
        assert all(set(item) == {"responder_id", "incident_id", "path", "time"} for item in plan)


def test_opgeslagen_outputs_komen_overeen_met_de_huidige_default(generated_outputs):
    """De ingecheckte scenario- en resultoutputs volgen de HMM-default."""
    root = Path(__file__).parents[1]
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        for generated, stored in (
            (generated_outputs[name][1], root / "Scenarios" / name / "plan.json"),
            (generated_outputs[name][2], root / "Scenarios" / name / "statistics.txt"),
            (generated_outputs[name][1], root / "results" / name / "plan.json"),
            (generated_outputs[name][2], root / "results" / name / "statistics.txt"),
        ):
            assert generated.read_text() == stored.read_text(), stored
