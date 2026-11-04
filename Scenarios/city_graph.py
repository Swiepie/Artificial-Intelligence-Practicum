from dataclasses import dataclass

from .road import Road

@dataclass(frozen=True, slots=True)
class Node:
    id: str
    name: str
    x: float
    y: float
    type: str


@dataclass(frozen=True, slots=True)
class CityGraph:
    nodes: dict[str, Node]
    roads: tuple[Road, ...]

    def __post_init__(self) -> None:
        for road in self.roads:
            if road.from_node not in self.nodes or road.to_node not in self.nodes:
                raise ValueError(f"Road references an unknown node: {road}")

    def outgoing_roads(self, node_id: str) -> tuple[Road, ...]:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node: {node_id}")
        return tuple(road for road in self.roads if road.from_node == node_id)

    def get_road(self, from_node: str, to_node: str) -> Road:
        for road in self.outgoing_roads(from_node):
            if road.to_node == to_node:
                return road
        raise KeyError(f"No road from {from_node} to {to_node}")
