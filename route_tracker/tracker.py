#!/usr/bin/env python3
import sys
from pathlib import Path
from subprocess import run
from typing import List, MutableMapping, Sequence, Tuple, cast

from tomlkit import document, dumps, parse
from typer import Exit, Typer, echo
from xdg import xdg_config_home, xdg_data_home

from route_tracker.graph import (Graph, add_edge, add_node, add_selected_node,
                                 deselect_node, draw, mark_edge, select_node,
                                 store)

app = Typer()


@app.command()
def new(name: str) -> None:
    if _get_graph_file(name).exists():
        echo(f'{name} already exists. Ignoring...', err=True)
        raise Exit(code=1)
    _create_new_graph(name)
    _store_choice_info(name, 0, 0)


def _get_graph_file(name: str) -> Path:
    return _get_project_dir(name) / 'graph'


def _get_project_dir(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker' / name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _create_new_graph(name: str) -> None:
    graph = Graph(name)
    add_selected_node(graph, 0, '0. start')
    store(graph, _get_graph_file(name))
    echo(f'{name} created')


def _store_choice_info(project_name: str, last_choice: int, last_id: int) \
        -> None:
    with open(_get_project_dir(project_name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc['last_selected_choice'] = last_choice
        doc['last_id'] = last_id
        f.write(dumps(doc))


@app.command()
def add(project_name: str) -> None:
    _get_graph(project_name)
    choices = _read_choices()
    selected_choice_index = _get_selected_choice_index(len(choices))
    add_choices_and_selection(project_name, choices, selected_choice_index)


def add_choices_and_selection(project_name: str, choices: Sequence[str],
                              selected_choice_index: int) -> None:
    graph, choices_ids = _add_choices_to_graph(choices, project_name)
    selected_choice_id = choices_ids[selected_choice_index]
    last_choice = _get_last_selected_choice(project_name)
    _update_selections(graph, last_choice, selected_choice_id)
    store(graph, _get_graph_file(project_name))
    _store_choice_info(project_name, selected_choice_id, choices_ids[-1])


def _get_graph(name: str) -> Graph:
    try:
        graph = Graph(_get_graph_file(name))
    except FileNotFoundError:
        echo(f'Project {name} does not exist', err=True)
        raise Exit(code=1)
    return graph


def _read_choices() -> List[str]:
    echo('Enter available choices separated by newlines. A blank line ends the'
         ' input')
    choices: List[str] = []
    while (line := sys.stdin.readline()) != '\n':
        choices.append(line.rstrip())
    if not choices:
        echo('At least one choice must be entered', err=True)
        raise Exit(code=1)
    return choices


def _get_selected_choice_index(choices_number: int) -> int:
    index_input = input('Enter the zero-based index of your selection\n')
    try:
        index = int(index_input)
    except ValueError:
        echo(f'Index {index_input} is not a number', err=True)
        raise Exit(code=1)
    if index < 0 or index >= choices_number:
        echo(f'Index {index} is out of bounds', err=True)
        raise Exit(code=1)
    return index


def _add_choices_to_graph(choices: Sequence[str], project_name: str) \
        -> Tuple[Graph, Sequence[int]]:
    next_id = _get_last_id(project_name) + 1
    choices_ids = list(range(next_id, next_id + len(choices)))
    graph = _get_graph(project_name)
    last_selected_choice = _get_last_selected_choice(project_name)
    for choice_label, choice_id in zip(choices, choices_ids):
        add_node(graph, choice_id, label=f'{choice_id}. {choice_label}')
        add_edge(graph, last_selected_choice, choice_id)
    return graph, choices_ids


def _get_last_id(name: str) -> int:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_id'])


def _get_last_selected_choice(name: str) -> int:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_selected_choice'])


def _update_selections(
        graph: Graph, last_choice: int, selected_choice: int,
) -> None:
    deselect_node(graph, last_choice)
    select_node(graph, selected_choice)
    mark_edge(graph, last_choice, selected_choice)


@app.command()
def view(project_name: str) -> None:
    routes_file = _get_project_dir(project_name) / 'routes.png'
    draw(_get_graph(project_name), routes_file)
    run([_get_viewer(), routes_file])


def _get_viewer() -> str:
    try:
        viewer = _read_viewer()
    except KeyError:
        viewer = input('Image viewer command:')
        _store_viewer(viewer)
    return viewer


def _read_viewer() -> str:
    return _read_config()['viewer']


def _read_config() -> MutableMapping[str, str]:
    try:
        with open(_get_config(), 'r') as f:
            config = parse(f.read())
    except FileNotFoundError:
        config = document()
    return config


def _get_config() -> Path:
    config_dir = xdg_config_home() / 'route-tracker'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.toml'


def _store_viewer(viewer: str) -> None:
    config = _read_config()
    config['viewer'] = viewer
    with open(_get_config(), 'w') as f:
        f.write(dumps(config))
