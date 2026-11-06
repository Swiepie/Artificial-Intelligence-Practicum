from collections import defaultdict
from typing import Iterable

from input_data.road import Road
from input_data.traffic import TrafficLevel, TrafficObservation, TrafficProbabilities


class TrafficHMM:
    """HMM voor forward filtering, voorspelling en Viterbi per weg."""

    def __init__(
        self,
        probabilities: TrafficProbabilities,
        observations: Iterable[TrafficObservation],
    ) -> None:
        """Groepeer en sorteer historische waarnemingen per gerichte weg."""
        self.probabilities = probabilities
        self.observations: dict[tuple[str, str], tuple[TrafficObservation, ...]] = {}
        grouped: dict[tuple[str, str], list[TrafficObservation]] = defaultdict(list)
        for observation in observations:
            grouped[(observation.from_node, observation.to_node)].append(observation)
        for key, values in grouped.items():
            self.observations[key] = tuple(
                sorted(values, key=lambda item: item.observation_nr)
            )

    def filter(self, road: Road) -> dict[TrafficLevel, float]:
        """Bereken de huidige verkeersbelief met forward filtering."""
        belief = dict(self.probabilities.initial)
        observations = self.observations.get((road.from_node, road.to_node), ())
        for observation in observations:
            updated = {
                state: belief[state]
                * self.probabilities.emission[state][observation.traffic]
                for state in TrafficLevel
            }
            belief = self._normalise(updated)
        return self._normalise(belief)

    def predict(self, road: Road, steps: int = 1) -> dict[TrafficLevel, float]:
        """Voorspel het verkeer een aantal stappen vooruit."""
        if steps < 0:
            raise ValueError("steps must be non-negative")
        belief = self.filter(road)
        for _ in range(steps):
            belief = self._predict(belief)
        return belief

    def viterbi(self, road: Road) -> tuple[TrafficLevel, ...]:
        """Geef de meest waarschijnlijke verborgen toestandsreeks terug."""
        observations = self.observations.get((road.from_node, road.to_node), ())
        if not observations:
            return (max(self.probabilities.initial, key=self.probabilities.initial.get),)
        scores = {
            state: self._log(self.probabilities.initial[state])
            + self._log(self.probabilities.emission[state][observations[0].traffic])
            for state in TrafficLevel
        }
        paths = {state: [state] for state in TrafficLevel}
        for observation in observations[1:]:
            next_scores = {}
            next_paths = {}
            for target in TrafficLevel:
                source = max(
                    TrafficLevel,
                    key=lambda candidate: scores[candidate]
                    + self._log(self.probabilities.transition[candidate][target]),
                )
                next_scores[target] = (
                    scores[source]
                    + self._log(self.probabilities.transition[source][target])
                    + self._log(self.probabilities.emission[target][observation.traffic])
                )
                next_paths[target] = paths[source] + [target]
            scores, paths = next_scores, next_paths
        return tuple(paths[max(scores, key=scores.get)])

    def _predict(self, belief: dict[TrafficLevel, float]) -> dict[TrafficLevel, float]:
        """Pas de overgangsmatrix toe op één verkeersbelief."""
        return self._normalise(
            {
                target: sum(
                    belief[source]
                    * self.probabilities.transition[source][target]
                    for source in TrafficLevel
                )
                for target in TrafficLevel
            }
        )

    @staticmethod
    def _normalise(values: dict[TrafficLevel, float]) -> dict[TrafficLevel, float]:
        """Normaliseer kansen zodat hun som precies één is."""
        total = sum(values.values())
        if total == 0:
            raise ValueError("HMM belief has zero probability")
        return {key: value / total for key, value in values.items()}

    @staticmethod
    def _log(value: float) -> float:
        """Bereken een logaritme en behandel nul als negatieve oneindigheid."""
        import math

        return math.log(value) if value > 0 else float("-inf")
