"""Regressiecontrole voor de gegenereerde scenario-uitvoer."""

import json


def test_scenario_plannen_zijn_deterministisch_vormgegeven(generated_outputs):
    """Doel / Input: plan.json van S1-S3 / Verwacht: lijst met vaste sleutels."""
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        plan = json.loads(generated_outputs[name][1].read_text())
        assert all(set(item) == {"responder_id", "incident_id", "path", "time"} for item in plan)
