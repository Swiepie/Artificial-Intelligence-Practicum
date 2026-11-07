"""Tests voor gerichte routezoektochten."""

from algorithms.routing import astar, uniform_cost_search
from algorithms.bayesian_road import BayesianRoadEstimator, RoadBelief
from algorithms.hmm_traffic import TrafficHMM
from input_data.road import RoadStatus
from input_data.city_graph import CityGraph, Node
from input_data.road import Road


def _graph():
    nodes = {
        name: Node(name, name, float(index), 0.0, "normal")
        for index, name in enumerate(("A", "B", "C", "D"))
    }
    return CityGraph(
        nodes,
        (
            Road("A", "B", 10, "street", 1),
            Road("B", "D", 10, "street", 1),
            Road("A", "C", 5, "street", 1),
            Road("C", "D", 30, "street", 1),
        ),
    )


def test_kortste_pad():
    """Doel / Input: mini-graaf / Verwacht: A-B-D met kost 20 / Faalt nu? nee."""
    graph = _graph()
    result = uniform_cost_search(graph, "A", "D", lambda road: road.normal_travel_time)
    assert result.path == ("A", "B", "D")
    assert result.cost == 20


def test_start_is_doel_en_onbereikbaar():
    """Doel / Input: start/doel en ontbrekende richting / Verwacht: 0 en onbereikbaar."""
    graph = _graph()
    assert astar(graph, "A", "A", lambda road: road.normal_travel_time).cost == 0
    assert not astar(graph, "D", "A", lambda road: road.normal_travel_time).reachable


def test_gerichtheid():
    """Doel / Input: D naar A / Verwacht: onbereikbaar / Faalt nu? nee."""
    assert not uniform_cost_search(
        _graph(), "D", "A", lambda road: road.normal_travel_time
    ).reachable


def test_astar_gelijk_aan_ucs():
    """Doel / Input: alle mini-graafparen / Verwacht: gelijke kosten / Faalt nu? nee."""
    graph = _graph()
    for start in graph.nodes:
        for goal in graph.nodes:
            astar_result = astar(graph, start, goal, lambda road: road.normal_travel_time)
            ucs_result = uniform_cost_search(
                graph, start, goal, lambda road: road.normal_travel_time
            )
            assert astar_result.cost == ucs_result.cost


def test_geblokkeerde_weg_wordt_vermeden():
    """Doel / Input: B->D geblokkeerd / Verwacht: A-C-D / Faalt nu? nee."""
    graph = _graph()
    beliefs = {
        ("A", "B"): RoadBelief("A", "B", {
            RoadStatus.OPEN: 1.0, RoadStatus.CONGESTED: 0.0, RoadStatus.BLOCKED: 0.0
        }, None),
        ("B", "D"): RoadBelief("B", "D", {
            RoadStatus.OPEN: 0.1, RoadStatus.CONGESTED: 0.0, RoadStatus.BLOCKED: 0.9
        }, None),
        ("A", "C"): RoadBelief("A", "C", {
            RoadStatus.OPEN: 1.0, RoadStatus.CONGESTED: 0.0, RoadStatus.BLOCKED: 0.0
        }, None),
        ("C", "D"): RoadBelief("C", "D", {
            RoadStatus.OPEN: 1.0, RoadStatus.CONGESTED: 0.0, RoadStatus.BLOCKED: 0.0
        }, None),
    }
    from algorithms.routing import RoadCostModel
    result = astar(graph, "A", "D", RoadCostModel(graph, beliefs).cost)
    assert result.path == ("A", "C", "D")


def test_afstand_minstens_euclidisch(scenario3):
    """Doel / Input: alle S3-wegen / Verwacht: distance >= Euclidisch / Faalt nu? nee."""
    import math
    for road in scenario3.graph.roads:
        start = scenario3.graph.nodes[road.from_node]
        end = scenario3.graph.nodes[road.to_node]
        assert road.distance + 1e-9 >= math.hypot(start.x - end.x, start.y - end.y)


def test_astar_gelijk_aan_ucs_alle_scenario_paren(scenario1, scenario2, scenario3):
    """Doel / Input: alle S1-S3-paren / Verwacht: kostenverschil < 1e-6 / Faalt nu? nee."""
    from algorithms.bayesian_road import BayesianRoadEstimator
    from algorithms.hmm_traffic import TrafficHMM
    from algorithms.routing import RoadCostModel

    for scenario in (scenario1, scenario2, scenario3):
        beliefs = BayesianRoadEstimator(
            scenario.road_probabilities, scenario.road_reports
        ).estimate_all(scenario.graph.roads)
        model = RoadCostModel(
            scenario.graph,
            beliefs,
            TrafficHMM(
                scenario.traffic_probabilities, scenario.traffic_observations
            ),
        )
        nodes = tuple(scenario.graph.nodes)
        for start in nodes:
            for goal in nodes:
                astar_result = astar(
                    scenario.graph, start, goal, model.cost, model.travel_time
                )
                ucs_result = uniform_cost_search(
                    scenario.graph, start, goal, model.cost, model.travel_time
                )
                if astar_result.reachable or ucs_result.reachable:
                    assert abs(astar_result.cost - ucs_result.cost) < 1e-6
                else:
                    assert not astar_result.reachable and not ucs_result.reachable
