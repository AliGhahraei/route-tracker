#!/usr/bin/env python3
from pathlib import Path
from typing import Any, Union, cast

import pygraphviz as pgv

SELECTED_NODE_ATTRS = {'peripheries': 2, 'color': 'black:invis:black'}


class Graph:
    def __init__(self, name_or_path: Union[str, Path]):
        self._graph = (pgv.AGraph(name_or_path)
                       if isinstance(name_or_path, Path)
                       else pgv.AGraph(name=name_or_path, directed=True,
                                       forcelabels='true'))

    def __eq__(self, other: Any) -> bool:
        try:
            other_content: str = getattr(other, 'content')
        except AttributeError:
            return NotImplemented
        return self.content == other_content

    @property
    def content(self) -> str:
        return cast(str, self._graph.to_string())


def add_node(graph: Graph, node_id: int, label: str) -> None:
    graph._graph.add_node(node_id, label=label)


def add_selected_node(graph: Graph, node_id: int, label: str) -> None:
    graph._graph.add_node(node_id, label=label, **SELECTED_NODE_ATTRS)


def add_edge(graph: Graph, starting_id: int, ending_id: Union[int, str],
             color: str = 'black') -> None:
    graph._graph.add_edge(starting_id, ending_id, color=color)


def add_ending_node(graph: Graph, node_id: str, label: str) -> None:
    graph._graph.add_node(node_id, label=label, fontcolor='white',
                          fillcolor='black', style='filled')


def deselect_node(graph: Graph, node_id: int) -> None:
    node = graph._graph.get_node(node_id)
    del node.attr['peripheries']
    del node.attr['color']


def verify_id_exists(graph: Graph, node_id: Union[int, str]) -> None:
    _get_node(graph, node_id)


def _get_node(graph: Graph, node_id: Union[int, str]) -> pgv.Node:
    try:
        node = graph._graph.get_node(node_id)
    except KeyError:
        raise InvalidNodeId(node_id)
    return node


class InvalidNodeId(Exception):
    def __init__(self, node_id: Union[int, str]):
        self.node_id = node_id
        super().__init__(node_id)


def select_node(graph: Graph, node_id: int) -> None:
    node = _get_node(graph, node_id)
    node.attr.update(SELECTED_NODE_ATTRS)


def mark_edge(graph: Graph, starting_id: int, ending_id: int, color: str) \
        -> None:
    graph._graph.get_edge(starting_id, ending_id).attr['color'] = color


def comment_node(graph: Graph, node_id: int, comment: str) -> None:
    _get_node(graph, node_id).attr['xlabel'] = comment


def store(graph: Graph, path: Path) -> None:
    graph._graph.write(path)


def draw(graph: Graph, path: Path) -> None:
    graph._graph.draw(path, prog='dot')
