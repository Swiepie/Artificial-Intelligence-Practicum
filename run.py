"""Officieel startpunt voor het noodhulpsysteem."""

import argparse
from pathlib import Path

from algorithms.output import PlanWriter, StatisticsWriter
from algorithms.simulation import Simulator
from algorithms.independent_validator import IndependentPlanValidator
from input_data.scenario_loader import ScenarioLoader


def run_scenario(scenario_name: str, output_dir: Path | None = None) -> None:
    """Genereer de uitvoerbestanden voor één scenario."""
    scenario_directory = Path(__file__).parent / "Scenarios" / scenario_name
    if not scenario_directory.is_dir():
        raise ValueError(f"Scenario directory does not exist: {scenario_directory}")
    scenario = ScenarioLoader().load(scenario_directory)
    result = Simulator().run(scenario)
    output_directory = output_dir or scenario_directory
    plan_path = output_directory / "plan.json"
    PlanWriter().write(plan_path, result, scenario)
    statistics_path = output_directory / "statistics.txt"
    StatisticsWriter().write_from_plan(statistics_path, plan_path, scenario)
    issues = IndependentPlanValidator().validate(plan_path, scenario_directory)
    print(
        f"{scenario_name}: loaded {len(scenario.graph.nodes)} nodes, "
        f"{len(scenario.graph.roads)} roads, "
        f"{len(scenario.responders)} responders, and "
        f"{len(scenario.incidents)} incidents."
    )
    print(
        f"{scenario_name}: assigned {len(result.assignments)} incidents, "
        f"left {len(result.unassigned_incidents)} unassigned."
    )
    if issues:
        print(
            f"{scenario_name}: warning: independent validation found "
            + "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        )


def main() -> None:
    """Lees het scenarioargument en genereer de uitvoerbestanden."""
    parser = argparse.ArgumentParser(
        description="Generate plan.json and statistics.txt for a scenario."
    )
    parser.add_argument("scenario", nargs="?")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Map voor plan.json en statistics.txt; standaard de scenariomap.",
    )
    args = parser.parse_args()
    if args.scenario:
        try:
            run_scenario(args.scenario, args.output_dir)
        except ValueError as error:
            parser.error(str(error))
    else:
        if args.output_dir:
            parser.error("--output-dir requires an explicit scenario")
        for scenario_name in ("Scenario1", "Scenario2", "Scenario3"):
            try:
                run_scenario(scenario_name)
            except ValueError as error:
                parser.error(str(error))


if __name__ == "__main__":
    main()
