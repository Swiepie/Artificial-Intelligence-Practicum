"""Tests voor validatie die de opgeslagen Assignment-objecten niet gebruikt."""

import json
from pathlib import Path

from algorithms.independent_validator import IndependentPlanValidator


def test_regenerated_plans_have_no_optimistic_errors():
    """Doel / Input: plan.json van S1-S3 / Verwacht: geen optimistische fouten."""
    validator = IndependentPlanValidator()
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        directory = __import__("pathlib").Path("Scenarios") / name
        issues = validator.validate(directory / "plan.json", directory)
        assert not [
            issue for issue in issues if issue.code.endswith("_optimistic")
        ], (name, issues)


def test_validator_gebruikt_tijdvolgorde_voor_responderlocatie(tmp_path):
    """Doel / Input: S2-plan met omgekeerde JSON-volgorde / Verwacht: geen wrong_origin."""
    scenario_dir = Path("Scenarios/Scenario2")
    plan = json.loads((scenario_dir / "plan.json").read_text())
    responder_items = [item for item in plan if item["responder_id"] == "R1"]
    assert len(responder_items) >= 2
    reversed_items = list(reversed(responder_items))
    iterator = iter(reversed_items)
    reordered = [
        next(iterator) if item["responder_id"] == "R1" else item
        for item in plan
    ]
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(reordered))
    issues = IndependentPlanValidator().validate(plan_path, scenario_dir)
    assert not [issue for issue in issues if issue.code == "wrong_origin"]


def test_validator_meldt_schema_en_padfouten(tmp_path):
    """Doel / Input: lege pad en ontbrekende sleutel / Verwacht: schema- en empty_path."""
    scenario_dir = Path("Scenarios/Scenario1")
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps([
        {"responder_id": "R1", "incident_id": "I1", "path": [], "time": 0},
        {"responder_id": "R1", "incident_id": "I2", "path": ["N1"]},
    ]))
    issues = IndependentPlanValidator().validate(plan_path, scenario_dir)
    codes = {issue.code for issue in issues}
    assert "empty_path" in codes
    assert "schema" in codes
