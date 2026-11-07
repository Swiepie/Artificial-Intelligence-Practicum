import heapq
import math
from dataclasses import dataclass
from itertools import count
from typing import Callable, Mapping

from input_data.city_graph import CityGraph
from input_data.road import Road, RoadStatus
from input_data.traffic import TrafficLevel
from .bayesian_road import RoadBelief
from .constants import BLOCKED_PROBABILITY_THRESHOLD
from .hmm_traffic import TrafficHMM


@dataclass(frozen=True, slots=True)
class RouteResult:
    path: tuple[str, ...]
    cost: float
    reachable: bool = True
    travel_time: float | None = None

    def __post_init__(self) -> None:
        """Gebruik de zoekkost als reistijd wanneer geen aparte tijd is gegeven."""
        if self.travel_time is None:
            object.__setattr__(self, "travel_time", self.cost)


class RoadCostModel:
    """Combineer Bayesiaans wegrisico en HMM-verkeer tot één randkost."""

    def __init__(
        self,
        graph: CityGraph,
        road_beliefs: Mapping[tuple[str, str], RoadBelief],
        traffic_hmm: TrafficHMM | None = None,
        blocked_penalty: float = 10_000.0,
        traffic_multipliers: Mapping[TrafficLevel, float] | None = None,
        use_map_status: bool = False,
    ) -> None:
        """Stel de gecombineerde weg-, risico- en verkeerskosten in.

        Een weg met meer dan de gedeelde blokkeerdrempel is voor routing
        onbruikbaar. Medium en High verkeer hebben factor 1.5.
        """
        self.graph = graph
        self.road_beliefs = road_beliefs
        self.traffic_hmm = traffic_hmm
        self.blocked_penalty = blocked_penalty
        self.traffic_multipliers = traffic_multipliers or {
            TrafficLevel.LOW: 1.0,
            TrafficLevel.MEDIUM: 1.5,
            TrafficLevel.HIGH: 1.5,
        }
        self.use_map_status = use_map_status

    def cost(self, road: Road) -> float:
        """Bereken de routezoekkost voor één weg."""
        belief = self._effective_belief(road)
        if self.use_map_status:
            status = belief.most_likely_status
            status_multiplier = {
                RoadStatus.OPEN: 1.0,
                RoadStatus.CONGESTED: 1.5,
                RoadStatus.BLOCKED: 1.0,
            }[status]
            blocked = self.blocked_penalty if status is RoadStatus.BLOCKED else 0.0
        else:
            if belief.blocked_probability > BLOCKED_PROBABILITY_THRESHOLD:
                return float("inf")
            status_multiplier = belief.expected_status_multiplier()
            blocked = self.blocked_penalty * belief.blocked_probability
        traffic_multiplier = 1.0
        if self.traffic_hmm is not None:
            traffic = self.traffic_hmm.predict(road)
            traffic_multiplier = sum(
                probability * self.traffic_multipliers[level]
                for level, probability in traffic.items()
            )
        # Beide bronnen beschrijven vertraging; neem de sterkste evidence om
        # dezelfde congestie niet tweemaal te vermenigvuldigen.
        delay_multiplier = max(status_multiplier, traffic_multiplier)
        return road.normal_travel_time * delay_multiplier + blocked

    def travel_time(self, road: Road) -> float:
        """Bereken de verwachte fysieke reistijd zonder blokkeerboete."""
        belief = self._effective_belief(road)
        if self.use_map_status:
            status = belief.most_likely_status
            if status is RoadStatus.BLOCKED:
                return float("inf")
            status_multiplier = 1.5 if status is RoadStatus.CONGESTED else 1.0
        else:
            status_multiplier = belief.expected_status_multiplier()
        traffic_multiplier = 1.0
        if self.traffic_hmm is not None:
            traffic = self.traffic_hmm.predict(road)
            traffic_multiplier = sum(
                probability * self.traffic_multipliers[level]
                for level, probability in traffic.items()
            )
        delay_multiplier = max(status_multiplier, traffic_multiplier)
        return road.normal_travel_time * delay_multiplier

    def _effective_belief(self, road: Road) -> RoadBelief:
        """Combineer Bayes met HMM-evidence zonder de blocked-status te verbergen."""
        belief = self.road_beliefs[(road.from_node, road.to_node)]
        if self.traffic_hmm is None:
            return belief
        traffic = self.traffic_hmm.predict(road)
        pressure = traffic[TrafficLevel.MEDIUM] + traffic[TrafficLevel.HIGH]
        return belief.with_traffic_evidence(pressure)


def _search(
    graph: CityGraph,
    start: str,
    goal: str,
    edge_cost: Callable[[Road], float],
    heuristic: Callable[[str], float],
    edge_time: Callable[[Road], float] | None = None,
) -> RouteResult:
    """Voer een algemene prioriteitszoektocht uit over de gerichte graaf."""
    if start not in graph.nodes or goal not in graph.nodes:
        raise KeyError(f"Unknown route endpoint: {start}, {goal}")
    sequence = count()
    queue = [(heuristic(start), next(sequence), 0.0, 0.0, start, (start,))]
    best = {start: 0.0}
    while queue:
        _, _, cost, _, node, path = heapq.heappop(queue)
        if node == goal:
            travel_time = sum(
                (edge_time or edge_cost)(graph.get_road(first, second))
                for first, second in zip(path, path[1:])
            )
            return RouteResult(path=path, cost=cost, travel_time=travel_time)
        if cost > best.get(node, float("inf")):
            continue
        for road in graph.outgoing_roads(node):
            next_cost = cost + edge_cost(road)
            if next_cost < best.get(road.to_node, float("inf")):
                best[road.to_node] = next_cost
                heapq.heappush(
                    queue,
                    (
                        next_cost + heuristic(road.to_node),
                        next(sequence),
                        next_cost,
                        0.0,
                        road.to_node,
                        path + (road.to_node,),
                    ),
                )
    return RouteResult(path=(), cost=float("inf"), reachable=False)


def astar(
    graph: CityGraph,
    start: str,
    goal: str,
    edge_cost: Callable[[Road], float],
    edge_time: Callable[[Road], float] | None = None,
) -> RouteResult:
    """Vind met A* de goedkoopste route met een toelaatbare heuristiek."""
    max_speed = max((road.speed for road in graph.roads), default=1.0)
    target = graph.nodes[goal]

    def heuristic(node_id: str) -> float:
        """Schat de resterende reistijd met Euclidische afstand."""
        node = graph.nodes[node_id]
        return math.hypot(node.x - target.x, node.y - target.y) / max_speed

    return _search(graph, start, goal, edge_cost, heuristic, edge_time)


def uniform_cost_search(
    graph: CityGraph,
    start: str,
    goal: str,
    edge_cost: Callable[[Road], float],
    edge_time: Callable[[Road], float] | None = None,
) -> RouteResult:
    """Vind met Uniform Cost Search de goedkoopste route zonder heuristiek."""
    return _search(graph, start, goal, edge_cost, lambda _: 0.0, edge_time)
