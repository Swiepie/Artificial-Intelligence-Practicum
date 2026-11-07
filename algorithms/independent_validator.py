"""Validatie van opgeslagen plannen zonder Assignment-objecten."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .bayesian_road import BayesianRoadEstimator
from input_data.scenario_loader import ScenarioLoader


@dataclass(frozen=True, slots=True)
class IndependentValidationIssue:
    """Een fout die rechtstreeks uit plan- en scenariobestanden is afgeleid."""

    code: str
    message: str


class IndependentPlanValidator:
    """Controleer een plan opnieuw met alleen persistente invoerbestanden."""

    def validate(
        self, plan_path: str | Path, scenario_directory: str | Path
    ) -> tuple[IndependentValidationIssue, ...]:
        """Geef alle schema-, route-, tijd- en capaciteitsfouten terug."""
        scenario_dir = Path(scenario_directory)
        scenario = ScenarioLoader().load(scenario_dir)
        with Path(plan_path).open(encoding="utf-8") as file:
            plan = json.load(file)
        if not isinstance(plan, list):
            return (IndependentValidationIssue("schema", "plan moet een lijst zijn"),)

        responders = {item.responder_id: item for item in scenario.responders}
        incidents = {item.incident_id: item for item in scenario.incidents}
        beliefs = BayesianRoadEstimator(
            scenario.road_probabilities, scenario.road_reports
        ).estimate_all(scenario.graph.roads)
        issues: list[IndependentValidationIssue] = []
        seen_incidents: set[str] = set()
        entries: dict[str, list[tuple[dict[str, Any], Any, Any, list[Any], float]]] = {}

        for index, assignment in enumerate(plan):
            prefix = f"assignment {index}"
            if not isinstance(assignment, dict) or set(assignment) != {
                "responder_id", "incident_id", "path", "time"
            }:
                issues.append(IndependentValidationIssue("schema", prefix))
                continue
            responder_id = assignment["responder_id"]
            incident_id = assignment["incident_id"]
            path = assignment["path"]
            start = assignment["time"]
            responder = responders.get(responder_id)
            incident = incidents.get(incident_id)
            if responder is None:
                issues.append(IndependentValidationIssue("unknown_responder", str(responder_id)))
                continue
            if incident is None:
                issues.append(IndependentValidationIssue("unknown_incident", str(incident_id)))
                continue
            if incident_id in seen_incidents:
                issues.append(IndependentValidationIssue("duplicate_incident", incident_id))
            seen_incidents.add(incident_id)
            if not isinstance(path, list) or not path:
                issues.append(IndependentValidationIssue("empty_path", incident_id))
                continue
            if isinstance(start, bool) or not isinstance(start, (int, float)) or start < 0:
                issues.append(IndependentValidationIssue("invalid_time", incident_id))
                continue
            entries.setdefault(responder_id, []).append(
                (assignment, responder, incident, path, float(start))
            )

        locations = {
            item.responder_id: item.start_location for item in scenario.responders
        }
        available = {
            item.responder_id: item.time_until_available for item in scenario.responders
        }
        schedules: dict[str, list[dict[str, float]]] = {}
        for responder_id, responder_entries in entries.items():
            for _, responder, incident, path, start in sorted(
                responder_entries, key=lambda item: item[4]
            ):
                if not responder.can_handle(incident.required_capability):
                    issues.append(IndependentValidationIssue("capability", incident.incident_id))
                if start < incident.timestamp:
                    issues.append(
                        IndependentValidationIssue("starts_before_known", incident.incident_id)
                    )
                if start < available[responder_id]:
                    issues.append(
                        IndependentValidationIssue("responder_unavailable", incident.incident_id)
                    )
                if path[0] != locations[responder_id]:
                    issues.append(
                        IndependentValidationIssue("wrong_origin", incident.incident_id)
                    )
                if path[-1] != incident.location:
                    issues.append(
                        IndependentValidationIssue("wrong_destination", incident.incident_id)
                    )

                normal_time = 0.0
                pessimistic_time = 0.0
                valid_path = True
                for first, second in zip(path, path[1:]):
                    try:
                        road = scenario.graph.get_road(first, second)
                    except KeyError:
                        issues.append(
                            IndependentValidationIssue(
                                "invalid_path", f"{first}->{second}"
                            )
                        )
                        valid_path = False
                        continue
                    belief = beliefs[(first, second)]
                    if belief.blocked_probability > 0.5:
                        issues.append(
                            IndependentValidationIssue(
                                "blocked_road", f"{first}->{second}"
                            )
                        )
                    normal_time += (
                        road.normal_travel_time * belief.expected_status_multiplier()
                    )
                    pessimistic_time += road.normal_travel_time * 1.5

                if valid_path and start + normal_time > incident.deadline:
                    issues.append(
                        IndependentValidationIssue(
                            "missed_deadline_optimistic", incident.incident_id
                        )
                    )
                if valid_path and start + pessimistic_time > incident.deadline:
                    issues.append(
                        IndependentValidationIssue(
                            "missed_deadline_pessimistic", incident.incident_id
                        )
                    )
                record = {
                    "start": start,
                    "completion": start + normal_time + incident.time_required,
                }
                schedules.setdefault(responder_id, []).append(record)
                locations[responder_id] = incident.location
                available[responder_id] = record["completion"]

        for responder_id, responder_schedule in schedules.items():
            ordered = sorted(responder_schedule, key=lambda item: item["start"])
            for previous, current in zip(ordered, ordered[1:]):
                if current["start"] < previous["completion"]:
                    issues.append(IndependentValidationIssue("overlap", responder_id))
        return tuple(issues)
