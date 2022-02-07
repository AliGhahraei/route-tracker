#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Sequence

from route_tracker.graph import (Graph, add_edge, add_ending_node, add_node,
                                 add_selected_node, deselect_node, mark_edge,
                                 select_node, verify_id_exists)

ROUTE_COLORS = ['green', 'blue']


@dataclass
class ProjectInfo:
    name: str
    graph: Graph
    last_choice_id: int
    last_generated_id: int
    next_ending_id: int


def create_project(name: str) -> ProjectInfo:
    return ProjectInfo(name, _create_graph(name), last_choice_id=0,
                       last_generated_id=0, next_ending_id=0)


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
              ROUTE_COLORS[info.next_ending_id])
    info.last_choice_id = selected_choice


def add_ending(info: ProjectInfo, ending_label: str, new_choice_id: int) \
        -> None:
    numeric_ending_id = info.next_ending_id
    ending_id = f'E{numeric_ending_id}'
    add_ending_node(info.graph, ending_id, f'{ending_id}. {ending_label}')
    last_selected_choice = info.last_choice_id
    add_edge(info.graph, last_selected_choice, ending_id,
             ROUTE_COLORS[numeric_ending_id])
    deselect_node(info.graph, last_selected_choice)
    select_node(info.graph, new_choice_id)
    info.last_choice_id = new_choice_id
    info.next_ending_id = numeric_ending_id + 1


def advance_to_choice(info: ProjectInfo, selected_id: int) -> None:
    deselect_node(info.graph, info.last_choice_id)
    select_node(info.graph, selected_id)
    add_edge(info.graph, info.last_choice_id, selected_id,
             ROUTE_COLORS[info.next_ending_id])
    info.last_choice_id = selected_id


def link_to_choice(info: ProjectInfo, selected_id: int) -> None:
    verify_id_exists(info.graph, selected_id)
    add_edge(info.graph, info.last_choice_id, selected_id)
