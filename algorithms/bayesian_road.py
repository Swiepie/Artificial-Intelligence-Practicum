from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping

from input_data.road import (
    Road,
    RoadProbabilities,
    RoadReport,
    RoadReportSource,
    RoadStatus,
    Weather,
)


@dataclass(frozen=True, slots=True)
class RoadBelief:
    """Posteriorverdeling van één gerichte wegtoestand."""

    from_node: str
    to_node: str
    probabilities: Mapping[RoadStatus, float]
    weather: Weather

    @property
    def most_likely_status(self) -> RoadStatus:
        """Geef de wegtoestand met de hoogste posterior terug."""
        return max(self.probabilities, key=self.probabilities.get)

    @property
    def blocked_probability(self) -> float:
        """Geef de kans terug dat de weg geblokkeerd is."""
        return self.probabilities[RoadStatus.BLOCKED]

    def expected_status_multiplier(self) -> float:
        """Bereken de verwachte reistijdvermenigvuldiger van de weg."""
        return (
            self.probabilities[RoadStatus.OPEN]
            + 1.5 * self.probabilities[RoadStatus.CONGESTED]
        )


class BayesianRoadEstimator:
    """Bereken exact P(status | weer, onafhankelijke meldingen)."""

    def __init__(
        self,
        probabilities: RoadProbabilities,
        reports: Iterable[RoadReport],
        default_weather: Weather | None = None,
    ) -> None:
        """Groepeer meldingen per gerichte weg en bepaal het standaardweer."""
        self.probabilities = probabilities
        self._reports: dict[tuple[str, str], list[RoadReport]] = defaultdict(list)
        for report in reports:
            self._reports[(report.from_node, report.to_node)].append(report)
        self.default_weather = default_weather or self._infer_weather()

    def _infer_weather(self) -> Weather:
        """Kies het meest voorkomende weer voor wegen zonder melding."""
        weather_counts: dict[Weather, int] = defaultdict(int)
        for reports in self._reports.values():
            for report in reports:
                weather_counts[report.weather] += 1
        return max(
            weather_counts,
            key=weather_counts.get,
            default=Weather.CLEAR,
        )

    def estimate(self, road: Road) -> RoadBelief:
        """Bereken de genormaliseerde posterior voor één gerichte weg."""
        reports = self._reports.get((road.from_node, road.to_node), ())
        weather = reports[0].weather if reports else self.default_weather
        posterior: dict[RoadStatus, float] = {}
        for status in RoadStatus:
            value = self.probabilities.road_status_given_weather[weather][status]
            for report in reports:
                value *= self.probabilities.report_likelihood[report.source][status][
                    report.reported_status
                ]
            posterior[status] = value
        total = sum(posterior.values())
        if total == 0:
            raise ValueError(f"Road probabilities have zero evidence for {road}")
        return RoadBelief(
            from_node=road.from_node,
            to_node=road.to_node,
            probabilities={status: value / total for status, value in posterior.items()},
            weather=weather,
        )

    def estimate_all(self, roads: Iterable[Road]) -> dict[tuple[str, str], RoadBelief]:
        """Bereken beliefs voor alle opgegeven wegen."""
        return {(road.from_node, road.to_node): self.estimate(road) for road in roads}
