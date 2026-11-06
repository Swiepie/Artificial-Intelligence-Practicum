import csv
import json
from pathlib import Path
from typing import Any

from .city_graph import CityGraph
from .city_graph import Node
from .incident import Incident, IncidentPriority
from .responder import Availability, Responder, ResponderType
from .road import (
    Road,
    RoadProbabilities,
    RoadReport,
    RoadReportSource,
    RoadStatus,
    Weather,
)
from .scenario_data import ScenarioData
from .traffic import TrafficLevel, TrafficObservation, TrafficProbabilities


class ScenarioLoader:
    """Lees één volledige scenariomap in als getypeerde domeinobjecten."""

    def load(self, scenario_directory: str | Path) -> ScenarioData:
        """Lees de graaf, entiteiten, observaties en kansmatrices in."""
        directory = Path(scenario_directory)
        graph = self._load_graph(directory / "city_graph.json")
        return ScenarioData(
            graph=graph,
            responders=self._load_responders(directory / "responders.csv", graph),
            incidents=self._load_incidents(directory / "incidents.csv", graph),
            road_reports=self._load_road_reports(directory / "road_reports.csv", graph),
            traffic_observations=self._load_traffic(directory / "observed_traffic.csv", graph),
            road_probabilities=self._load_road_probabilities(
                directory / "road_probabilities.json"
            ),
            traffic_probabilities=self._load_traffic_probabilities(
                directory / "traffic_probabilities.json"
            ),
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        """Lees één JSON-bestand en geef de inhoud als dictionary terug."""
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, str]]:
        """Lees één CSV-bestand en geef de rijen als dictionaries terug."""
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    @staticmethod
    def _load_graph(path: Path) -> CityGraph:
        """Bouw de gerichte stadsgraaf uit het JSON-bestand."""
        raw = ScenarioLoader._read_json(path)
        nodes = {
            item["id"]: Node(
                id=item["id"],
                name=item["name"],
                x=float(item["x"]),
                y=float(item["y"]),
                type=item["type"],
            )
            for item in raw["nodes"]
        }
        roads = tuple(
            Road(
                from_node=item["from"],
                to_node=item["to"],
                distance=float(item["distance"]),
                road_type=item["road_type"],
                speed=float(item["speed"]),
            )
            for item in raw["roads"]
        )
        return CityGraph(nodes=nodes, roads=roads)

    @staticmethod
    def _require_node(node_id: str, graph: CityGraph) -> str:
        """Controleer dat een verwijzing naar een bestaande knoop wijst."""
        if node_id not in graph.nodes:
            raise ValueError(f"Unknown node in scenario data: {node_id}")
        return node_id

    @staticmethod
    def _load_responders(path: Path, graph: CityGraph) -> tuple[Responder, ...]:
        """Lees responders en splits hun puntkomma-gescheiden vaardigheden."""
        return tuple(
            Responder(
                responder_id=row["responder_id"],
                type=ResponderType(row["type"]),
                start_location=ScenarioLoader._require_node(
                    row["start_location"], graph
                ),
                capabilities=frozenset(
                    capability.strip()
                    for capability in row["capabilities"].split(";")
                    if capability.strip()
                ),
                availability=Availability(row["availability"]),
                time_until_available=float(row["time_until_available"]),
            )
            for row in ScenarioLoader._read_csv(path)
        )

    @staticmethod
    def _load_incidents(path: Path, graph: CityGraph) -> tuple[Incident, ...]:
        """Lees incidenten en zet tekstvelden om naar domeintypes."""
        return tuple(
            Incident(
                incident_id=row["incident_id"],
                location=ScenarioLoader._require_node(row["location"], graph),
                priority=IncidentPriority(row["priority"]),
                deadline=float(row["deadline"]),
                required_capability=row["required_capability"],
                timestamp=float(row["timestamp"]),
                time_required=float(row["time_required"]),
            )
            for row in ScenarioLoader._read_csv(path)
        )

    @staticmethod
    def _load_road_reports(path: Path, graph: CityGraph) -> tuple[RoadReport, ...]:
        """Lees meldingen en controleer dat elke gemelde weg bestaat."""
        reports = []
        for row in ScenarioLoader._read_csv(path):
            graph.get_road(row["from"], row["to"])
            reports.append(
                RoadReport(
                    from_node=row["from"],
                    to_node=row["to"],
                    weather=Weather(row["weather"]),
                    source=RoadReportSource(row["source"]),
                    reported_status=RoadStatus(row["reported_status"]),
                )
            )
        return tuple(reports)

    @staticmethod
    def _load_traffic(path: Path, graph: CityGraph) -> tuple[TrafficObservation, ...]:
        """Lees historische verkeerswaarnemingen per gerichte weg."""
        observations = []
        for row in ScenarioLoader._read_csv(path):
            graph.get_road(row["from"], row["to"])
            observations.append(
                TrafficObservation(
                    observation_nr=int(row["observation_nr"]),
                    from_node=row["from"],
                    to_node=row["to"],
                    traffic=TrafficLevel(row["traffic_observation"]),
                )
            )
        return tuple(observations)

    @staticmethod
    def _load_road_probabilities(path: Path) -> RoadProbabilities:
        """Lees de Bayesiaanse kansmatrices voor wegtoestanden."""
        raw = ScenarioLoader._read_json(path)
        return RoadProbabilities(
            weather_prior={
                Weather(key): value for key, value in raw["weather_prior"].items()
            },
            road_status_given_weather={
                Weather(weather): {
                    RoadStatus(status): probability
                    for status, probability in values.items()
                }
                for weather, values in raw["road_status_given_weather"].items()
            },
            report_likelihood={
                RoadReportSource(source.removesuffix("_report").title()): {
                    RoadStatus(true_status): {
                        RoadStatus(reported_status): probability
                        for reported_status, probability in values.items()
                    }
                    for true_status, values in source_values.items()
                }
                for source, source_values in (
                    (key, value)
                    for key, value in raw.items()
                    if key.endswith("_report")
                )
            },
        )

    @staticmethod
    def _load_traffic_probabilities(path: Path) -> TrafficProbabilities:
        """Lees de begin-, overgangs- en emissiematrices van het HMM."""
        raw = ScenarioLoader._read_json(path)
        return TrafficProbabilities(
            initial={
                TrafficLevel(key): value for key, value in raw["initial"].items()
            },
            transition={
                TrafficLevel(state): {
                    TrafficLevel(next_state): probability
                    for next_state, probability in values.items()
                }
                for state, values in raw["transition"].items()
            },
            emission={
                TrafficLevel(state): {
                    TrafficLevel(observation): probability
                    for observation, probability in values.items()
                }
                for state, values in raw["emission"].items()
            },
        )
