from pathlib import Path

from Scenarios.scenario_loader import ScenarioLoader


def main() -> None:
    scenario = ScenarioLoader().load(Path(__file__).parent / "Scenario1")
    print(
        f"Loaded {len(scenario.graph.nodes)} nodes, "
        f"{len(scenario.graph.roads)} roads, "
        f"{len(scenario.responders)} responders, and "
        f"{len(scenario.incidents)} incidents."
    )


if __name__ == "__main__":
    main()