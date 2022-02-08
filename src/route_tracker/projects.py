#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from route_tracker.graph import (Graph, add_edge, add_ending_node, add_node,
                                 add_selected_node, comment_node,
                                 deselect_node, mark_edge, select_node,
                                 verify_id_exists)

_ROUTE_COLORS = (
    'green',
    'blue',
    'violet',
    'red',
    'orange',
    'yellow',
    'yellowgreen',
    'aquamarine4',
    'blueviolet',
    'deeppink3',
    'chocolate',
    'darkgoldenrod',
)


@dataclass
class _BaseInfo:
    name: str
    graph: Graph
    last_generated_id: int
    next_numeric_ending_id: int
    last_choice_id: int


@dataclass(kw_only=True)
class SaveFileInfo:
    route_id: int
    file: Optional[Path] = None
    target_directory: Optional[Path] = None


@dataclass
class ProjectInfo(SaveFileInfo, _BaseInfo):
    pass


def create_project(name: str, file: Optional[Path] = None,
                   target_dir: Optional[Path] = None) -> ProjectInfo:
    return ProjectInfo(name, _create_graph(name), last_choice_id=0,
                       last_generated_id=0, next_numeric_ending_id=0,
                       route_id=0, file=file, target_directory=target_dir)


def _create_graph(name: str) -> Graph:
    graph = Graph(name)
    add_selected_node(graph, 0, '0. start')
    return graph


def add_choices_and_selection(info: ProjectInfo, choices: Sequence[str],
                              selected_choice_index: int) -> None:
    choices_ids = _add_choices_to_graph(choices, info)
    selected_choice_id = choices_ids[selected_choice_index]
    _update_selection(info, selected_choice_id)
    info.last_generated_id = choices_ids[-1]


def _add_choices_to_graph(choices: Sequence[str], info: ProjectInfo) \
        -> Sequence[int]:
    next_id = info.last_generated_id + 1
    choices_ids = list(range(next_id, next_id + len(choices)))
    graph = info.graph
    last_selected_choice = info.last_choice_id
    for choice_label, choice_id in zip(choices, choices_ids):
        add_node(graph, choice_id, label=f'{choice_id}. {choice_label}')
        add_edge(graph, last_selected_choice, choice_id)
    return choices_ids


def _update_selection(
        info: ProjectInfo, selected_choice: int,
) -> None:
    deselect_node(info.graph, info.last_choice_id)
    select_node(info.graph, selected_choice)
    mark_edge(info.graph, info.last_choice_id, selected_choice,
              get_route_color(info))
    info.last_choice_id = selected_choice


def get_route_color(info: ProjectInfo) -> str:
    return _ROUTE_COLORS[info.route_id]


def add_ending(info: ProjectInfo, ending_label: str, new_choice_id: int) \
        -> None:
    ending_id = f'E{info.next_numeric_ending_id}'
    add_ending_node(info.graph, ending_id, f'{ending_id}. {ending_label}')
    _finish_route(info, ending_id, new_choice_id)
    info.next_numeric_ending_id += 1


def link_to_ending(info: ProjectInfo, ending_id: str, new_choice_id: int) \
        -> None:
    verify_id_exists(info.graph, ending_id)
    _finish_route(info, ending_id, new_choice_id)


def _finish_route(info: ProjectInfo, ending_id: str, new_choice_id: int) \
        -> None:
    last_selected_choice = info.last_choice_id
    deselect_node(info.graph, last_selected_choice)
    select_node(info.graph, new_choice_id)
    add_edge(info.graph, last_selected_choice, ending_id,
             get_route_color(info))
    info.last_choice_id = new_choice_id
    info.route_id += 1


def advance_to_choice(info: ProjectInfo, selected_id: int) -> None:
    deselect_node(info.graph, info.last_choice_id)
    select_node(info.graph, selected_id)
    add_edge(info.graph, info.last_choice_id, selected_id,
             get_route_color(info))
    info.last_choice_id = selected_id


def link_to_choice(info: ProjectInfo, selected_id: int) -> None:
    verify_id_exists(info.graph, selected_id)
    add_edge(info.graph, info.last_choice_id, selected_id)


def comment_choice(info: ProjectInfo, node_id: int, comment: str) -> None:
    comment_node(info.graph, node_id, f'{node_id}: {comment}')
