"""Tests voor validatie die de opgeslagen Assignment-objecten niet gebruikt."""

import json
from pathlib import Path

import pytest

from algorithms.independent_validator import IndependentPlanValidator


def test_regenerated_plans_have_no_optimistic_errors(generated_outputs):
    """Doel / Input: plan.json van S1-S3 / Verwacht: geen optimistische fouten."""
    validator = IndependentPlanValidator()
    for name in ("Scenario1", "Scenario2", "Scenario3"):
        directory = Path(__file__).parents[1] / "Scenarios" / name
        issues = validator.validate(generated_outputs[name][1], directory)
        assert not [
            issue for issue in issues if issue.code.endswith("_optimistic")
        ], (name, issues)


def test_validator_gebruikt_tijdvolgorde_voor_responderlocatie(tmp_path):
    """Een eigen plan toont dat JSON-volgorde niet de routevolgorde bepaalt."""
    scenario_dir = Path(__file__).parents[1] / "Scenarios" / "Scenario2"
    reordered = [
        {"responder_id": "R1", "incident_id": "I3",
         "path": ["N1", "N4", "N1", "N2"], "time": 30},
        {"responder_id": "R1", "incident_id": "I1",
         "path": ["H1", "N3", "H1", "N3", "N2", "N1"], "time": 0},
    ]
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(reordered))
    issues = IndependentPlanValidator().validate(plan_path, scenario_dir)
    assert not [issue for issue in issues if issue.code == "wrong_origin"]


def test_validator_meldt_schema_en_padfouten(tmp_path):
    """Doel / Input: lege pad en ontbrekende sleutel / Verwacht: schema- en empty_path."""
    scenario_dir = Path(__file__).parents[1] / "Scenarios" / "Scenario1"
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps([
        {"responder_id": "R1", "incident_id": "I1", "path": [], "time": 0},
        {"responder_id": "R1", "incident_id": "I2", "path": ["N1"]},
    ]))
    issues = IndependentPlanValidator().validate(plan_path, scenario_dir)
    codes = {issue.code for issue in issues}
    assert "empty_path" in codes
    assert "schema" in codes


@pytest.mark.parametrize(
    ("name", "plan", "expected"),
    [
        (
            "unknown-road",
            [{"responder_id": "R9", "incident_id": "I2",
              "path": ["N1", "N7"], "time": 0}],
            "invalid_path",
        ),
        (
            "wrong-capability",
            [{"responder_id": "R1", "incident_id": "I3",
              "path": ["H1", "N3", "H1", "N3", "N2"], "time": 0}],
            "capability",
        ),
        (
            "overlap",
            [
                {"responder_id": "R1", "incident_id": "I1",
                 "path": ["H1", "N3", "H1", "N3", "N2", "N1"], "time": 0},
                {"responder_id": "R1", "incident_id": "I3",
                 "path": ["N1", "N4", "N1", "N4", "N1", "N2"], "time": 0},
            ],
            "overlap",
        ),
        (
            "late-arrival",
            [{"responder_id": "R10", "incident_id": "I3",
              "path": ["N2"], "time": 100}],
            "missed_deadline_optimistic",
        ),
        (
            "wrong-origin",
            [{"responder_id": "R10", "incident_id": "I3",
              "path": ["N1", "N2"], "time": 0}],
            "wrong_origin",
        ),
        (
            "blocked-road",
            [{"responder_id": "R9", "incident_id": "I2",
              "path": ["N1", "N2", "N7"], "time": 0}],
            "blocked_road",
        ),
    ],
)
def test_validator_meldt_negatieve_plannen(tmp_path, name, plan, expected):
    """Iedere harde validatorvoorwaarde heeft een expliciete negatieve regressie."""
    scenario_dir = Path(__file__).parents[1] / "Scenarios" / "Scenario2"
    plan_path = tmp_path / f"{name}.json"
    plan_path.write_text(json.dumps(plan))
    codes = {
        issue.code
        for issue in IndependentPlanValidator().validate(plan_path, scenario_dir)
    }
    assert expected in codes
