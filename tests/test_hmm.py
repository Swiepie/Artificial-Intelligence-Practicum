"""Regressietests voor forward filtering van verkeer."""

import pytest

from algorithms.hmm_traffic import TrafficHMM
from input_data.road import Road
from input_data.traffic import TrafficLevel, TrafficObservation, TrafficProbabilities


def _hmm(observations):
    probabilities = TrafficProbabilities(
        initial={
            TrafficLevel.LOW: 0.5,
            TrafficLevel.MEDIUM: 0.35,
            TrafficLevel.HIGH: 0.15,
        },
        transition={
            TrafficLevel.LOW: {
                TrafficLevel.LOW: 0.75,
                TrafficLevel.MEDIUM: 0.22,
                TrafficLevel.HIGH: 0.03,
            },
            TrafficLevel.MEDIUM: {
                TrafficLevel.LOW: 0.15,
                TrafficLevel.MEDIUM: 0.70,
                TrafficLevel.HIGH: 0.15,
            },
            TrafficLevel.HIGH: {
                TrafficLevel.LOW: 0.03,
                TrafficLevel.MEDIUM: 0.22,
                TrafficLevel.HIGH: 0.75,
            },
        },
        emission={
            TrafficLevel.LOW: {
                TrafficLevel.LOW: 0.80,
                TrafficLevel.MEDIUM: 0.18,
                TrafficLevel.HIGH: 0.02,
            },
            TrafficLevel.MEDIUM: {
                TrafficLevel.LOW: 0.15,
                TrafficLevel.MEDIUM: 0.70,
                TrafficLevel.HIGH: 0.15,
            },
            TrafficLevel.HIGH: {
                TrafficLevel.LOW: 0.02,
                TrafficLevel.MEDIUM: 0.18,
                TrafficLevel.HIGH: 0.80,
            },
        },
    )
    return TrafficHMM(probabilities, observations)


def _road():
    return Road("A", "B", 1.0, "street", 1.0)


def test_filter_twee_observaties_met_transitie():
    """Doel / Input: Low, Medium / Verwacht: L=.3766 M=.5964 H=.0271 / Faalt nu? ja."""
    hmm = _hmm(
        [
            TrafficObservation(1, "A", "B", TrafficLevel.LOW),
            TrafficObservation(2, "A", "B", TrafficLevel.MEDIUM),
        ]
    )
    belief = hmm.filter(_road())
    assert belief[TrafficLevel.LOW] == pytest.approx(0.3766, abs=1e-4)
    assert belief[TrafficLevel.MEDIUM] == pytest.approx(0.5964, abs=1e-4)
    assert belief[TrafficLevel.HIGH] == pytest.approx(0.0271, abs=1e-4)


def test_filter_een_observatie():
    """Doel / Input: [Low] / Verwacht: .8782/.1153/.0066 / Faalt nu? nee."""
    belief = _hmm([TrafficObservation(1, "A", "B", TrafficLevel.LOW)]).filter(_road())
    assert belief[TrafficLevel.LOW] == pytest.approx(0.8782, abs=1e-4)
    assert belief[TrafficLevel.MEDIUM] == pytest.approx(0.1153, abs=1e-4)
    assert belief[TrafficLevel.HIGH] == pytest.approx(0.0066, abs=1e-4)


def test_filter_zonder_observaties():
    """Doel / Input: geen observaties / Verwacht: initial / Faalt nu? nee."""
    belief = _hmm([]).filter(_road())
    assert belief == {
        TrafficLevel.LOW: 0.5,
        TrafficLevel.MEDIUM: 0.35,
        TrafficLevel.HIGH: 0.15,
    }


def test_predict_voegt_een_stap_toe():
    """Doel / Input: predict(1) / Verwacht: filter × T en som 1 / Faalt nu? nee."""
    belief = _hmm([]).predict(_road(), steps=1)
    assert sum(belief.values()) == pytest.approx(1.0, abs=1e-9)
    assert belief[TrafficLevel.LOW] == pytest.approx(0.432, abs=1e-4)


def test_viterbi_lengte_en_low_reeks():
    """Doel / Input: drie Low-observaties / Verwacht: lengte 3 en Low-reeks / Faalt nu? nee."""
    observations = [
        TrafficObservation(index, "A", "B", TrafficLevel.LOW)
        for index in range(1, 4)
    ]
    path = _hmm(observations).viterbi(_road())
    assert len(path) == 3
    assert path == (TrafficLevel.LOW,) * 3


def test_hmm_normaliseert_alle_scenario_wegen(scenario1, scenario2, scenario3):
    """Doel / Input: alle S1-S3-wegen / Verwacht: belief-som 1 / Faalt nu? nee."""
    for scenario in (scenario1, scenario2, scenario3):
        hmm = TrafficHMM(
            scenario.traffic_probabilities, scenario.traffic_observations
        )
        for road in scenario.graph.roads:
            assert sum(hmm.filter(road).values()) == pytest.approx(1.0, abs=1e-9)


def test_onbekende_weg_valt_terug_op_initial(scenario3):
    """Doel / Input: S3-weg zonder observaties / Verwacht: initial x T / Faalt nu? nee."""
    observed = {
        (item.from_node, item.to_node)
        for item in scenario3.traffic_observations
    }
    road = next(
        road for road in scenario3.graph.roads
        if (road.from_node, road.to_node) not in observed
    )
    hmm = TrafficHMM(
        scenario3.traffic_probabilities, scenario3.traffic_observations
    )
    predicted = hmm.predict(road)
    assert predicted[TrafficLevel.LOW] == pytest.approx(0.53, abs=1e-4)
    assert sum(predicted.values()) == pytest.approx(1.0, abs=1e-9)
