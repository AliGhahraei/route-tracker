#!/usr/bin/env python3
import os
from pathlib import Path

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


@fixture(autouse=True)
def test_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path
    os.environ['XDG_DATA_HOME'] = str(data_dir)
    return data_dir
