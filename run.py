"""Officieel startpunt voor het noodhulpsysteem."""

import argparse
from pathlib import Path

from algorithms.output import PlanWriter, StatisticsWriter
from algorithms.simulation import Simulator
from algorithms.independent_validator import IndependentPlanValidator
from input_data.scenario_loader import ScenarioLoader


def main() -> None:
    """Lees het scenarioargument en genereer de twee uitvoerbestanden."""
    parser = argparse.ArgumentParser(
        description="Generate plan.json and statistics.txt for a scenario."
    )
    parser.add_argument("scenario", nargs="?", default="Scenario3")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Map voor plan.json en statistics.txt; standaard de scenariomap.",
    )
    args = parser.parse_args()
    scenario_directory = Path(__file__).parent / "Scenarios" / args.scenario
    if not scenario_directory.is_dir():
        parser.error(f"Scenario directory does not exist: {scenario_directory}")
    scenario = ScenarioLoader().load(scenario_directory)
    result = Simulator().run(scenario)
    output_directory = args.output_dir or scenario_directory
    plan_path = output_directory / "plan.json"
    PlanWriter().write(plan_path, result, scenario)
    statistics_path = output_directory / "statistics.txt"
    StatisticsWriter().write_from_plan(statistics_path, plan_path, scenario)
    issues = IndependentPlanValidator().validate(plan_path, scenario_directory)
    print(
        f"Loaded {len(scenario.graph.nodes)} nodes, "
        f"{len(scenario.graph.roads)} roads, "
        f"{len(scenario.responders)} responders, and "
        f"{len(scenario.incidents)} incidents."
    )
    print(
        f"Assigned {len(result.assignments)} incidents, "
        f"left {len(result.unassigned_incidents)} unassigned."
    )
    if issues:
        print(
            "Warning: independent validation found "
            + "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        )


if __name__ == "__main__":
    main()
