"""Regressietests voor status- en verkeerskosten."""

import pytest

from algorithms.bayesian_road import BayesianRoadEstimator
from algorithms.hmm_traffic import TrafficHMM
from algorithms.routing import RoadCostModel
from input_data.road import RoadStatus


def test_reistijd_n1_n2_conditioneel_op_niet_geblokkeerd(scenario2):
    """Doel / Input: S2 N1->N2 / Verwacht: circa 29.63 s / Faalt nu? ja."""
    estimator = BayesianRoadEstimator(
        scenario2.road_probabilities, scenario2.road_reports, default_weather=None
    )
    road = scenario2.graph.get_road("N1", "N2")
    belief = estimator.estimate(road)
    assert belief.blocked_probability == pytest.approx(0.8302, abs=1e-4)
    model = RoadCostModel(scenario2.graph, {("N1", "N2"): belief})
    assert model.travel_time(road) == pytest.approx(29.63, abs=0.05)
    assert model.cost(road) == float("inf")


def test_reistijd_nooit_onder_normaal(scenario1, scenario2, scenario3):
    """Doel / Input: alle wegen S1-S3 / Verwacht: vrije tijd >= normaal / Faalt nu? ja."""
    for scenario in (scenario1, scenario2, scenario3):
        estimator = BayesianRoadEstimator(
            scenario.road_probabilities, scenario.road_reports
        )
        beliefs = estimator.estimate_all(scenario.graph.roads)
        model = RoadCostModel(scenario.graph, beliefs)
        for road in scenario.graph.roads:
            assert model.travel_time(road) >= road.normal_travel_time


def test_verkeersfactor_blijft_binnen_opgavegrens(scenario3):
    """Doel / Input: alle wegen S3 / Verwacht: factor maximaal 1.5 / Faalt nu? ja."""
    estimator = BayesianRoadEstimator(scenario3.road_probabilities, scenario3.road_reports)
    beliefs = estimator.estimate_all(scenario3.graph.roads)
    model = RoadCostModel(scenario3.graph, beliefs, TrafficHMM(
        scenario3.traffic_probabilities, scenario3.traffic_observations
    ))
    for road in scenario3.graph.roads:
        if model.travel_time(road) != float("inf"):
            assert model.travel_time(road) <= 1.5 * road.normal_travel_time


def test_blokkeerstraf_wordt_meegenomen(scenario2):
    """Doel / Input: P(Blocked)=.8302 / Verwacht: penaltybijdrage >= 8302 / Faalt nu? nee."""
    road = scenario2.graph.get_road("N1", "N2")
    belief = BayesianRoadEstimator(
        scenario2.road_probabilities, scenario2.road_reports
    ).estimate(road)
    model = RoadCostModel(scenario2.graph, {("N1", "N2"): belief})
    assert model.cost(road) >= model.blocked_penalty * belief.blocked_probability


def test_map_modus_blocked_oneindig(scenario2):
    """Doel / Input: MAP=Blocked / Verwacht: inf / Faalt nu? nee."""
    road = scenario2.graph.get_road("N1", "N2")
    belief = BayesianRoadEstimator(
        scenario2.road_probabilities, scenario2.road_reports
    ).estimate(road)
    model = RoadCostModel(
        scenario2.graph, {("N1", "N2"): belief}, use_map_status=True
    )
    assert model.travel_time(road) == float("inf")
