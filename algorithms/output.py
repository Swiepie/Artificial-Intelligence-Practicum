import json
from pathlib import Path
from input_data.scenario_data import ScenarioData
from .allocation import Assignment
from .routing import build_road_cost_model
from .simulation import SimulationResult
from .validator import PlanValidator, ValidationIssue


class PlanWriter:
    """Valideer en schrijf de vereiste lijst met toewijzingen."""

    def write(
        self,
        path: str | Path,
        result: SimulationResult,
        scenario: ScenarioData,
    ) -> tuple[ValidationIssue, ...]:
        """Schrijf plan.json alleen wanneer alle toewijzingen geldig zijn."""
        issues = PlanValidator().validate(
            result.assignments,
            scenario.graph,
            scenario.responders,
            scenario.incidents,
        )
        if issues:
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"Refusing to write an invalid plan: {details}")

        payload = [
            {
                "responder_id": assignment.responder.responder_id,
                "incident_id": assignment.incident.incident_id,
                "path": list(assignment.route.path),
                "time": assignment.start_time,
            }
            for assignment in result.assignments
        ]
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return issues


class StatisticsWriter:
    """Schrijf statistieken in seconden; onbehandeld betekent deadline gemist."""

    def write(
        self,
        path: str | Path,
        result: SimulationResult,
        scenario: ScenarioData,
    ) -> None:
        """Bereken en schrijf de verplichte systeemprestatiestatistieken."""
        assignments = result.assignments
        handled = len(assignments)
        responders_used = len(
            {assignment.responder.responder_id for assignment in assignments}
        )
        average_response = (
            sum(assignment.response_time for assignment in assignments) / handled
            if handled
            else 0.0
        )
        deadlines_met = sum(
            1
            for assignment in assignments
            if assignment.arrival_time <= assignment.incident.deadline
        )
        total_incidents = len(scenario.incidents)
        percentage_met = (
            100.0 * deadlines_met / total_incidents if total_incidents else 100.0
        )
        text = "\n".join(
            [
                "System statistics:",
                f"* {handled} incidents handled",
                f"* {responders_used} responders used",
                f"* Average response time: {average_response:.1f} s",
                f"* Deadlines met: {percentage_met:.1f}%",
                "",
                "Calculation notes:",
                "* Response time is arrival time minus incident timestamp.",
                "* Average response time includes handled incidents only.",
                "* Unhandled incidents count as missed deadlines.",
                "* Time units are simulation seconds.",
            ]
        )
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")

    def write_from_plan(
        self,
        path: str | Path,
        plan_path: str | Path,
        scenario: ScenarioData,
    ) -> None:
        """Bereken statistieken opnieuw uit plan.json en scenariobestanden."""
        with Path(plan_path).open(encoding="utf-8") as file:
            plan = json.load(file)
        incidents = {incident.incident_id: incident for incident in scenario.incidents}
        cost_model = build_road_cost_model(scenario)
        response_times: list[float] = []
        deadlines_met = 0
        for assignment in plan:
            incident = incidents[assignment["incident_id"]]
            travel_time = sum(
                cost_model.travel_time(scenario.graph.get_road(first, second))
                for first, second in zip(assignment["path"], assignment["path"][1:])
            )
            arrival = assignment["time"] + travel_time
            response_times.append(arrival - incident.timestamp)
            if arrival <= incident.deadline:
                deadlines_met += 1
        handled = len(plan)
        responders_used = len({assignment["responder_id"] for assignment in plan})
        average_response = sum(response_times) / handled if handled else 0.0
        total_incidents = len(scenario.incidents)
        percentage_met = (
            100.0 * deadlines_met / total_incidents if total_incidents else 100.0
        )
        text = "\n".join(
            [
                "System statistics:",
                f"* {handled} incidents handled",
                f"* {responders_used} responders used",
                f"* Average response time: {average_response:.1f} s",
                f"* Deadlines met: {percentage_met:.1f}%",
                "",
                "Calculation notes:",
                "* Response time is arrival time minus incident timestamp.",
                "* Average response time includes handled incidents only.",
                "* Unhandled incidents count as missed deadlines.",
                "* Time units are simulation seconds.",
            ]
        )
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
