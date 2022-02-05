#!/usr/bin/env python3
from pytest import fixture

from route_tracker.graph import Graph, add_node


@fixture
def starting_graph(empty_graph: Graph) -> Graph:
    graph = empty_graph
    add_node(graph, 0, '0. start')
    return graph


@fixture
def empty_graph() -> Graph:
    return Graph('test_name')
