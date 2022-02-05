#!/usr/bin/env python3
import sys
from pathlib import Path
from subprocess import run
from typing import List, MutableMapping, cast

from tomlkit import document, dumps, parse
from typer import Exit, Typer, echo
from xdg import xdg_config_home, xdg_data_home

from route_tracker.graph import Graph, draw, store
from route_tracker.projects import (ProjectInfo, add_choices_and_selection,
                                    create_project)

app = Typer()


@app.command()
def new(name: str) -> None:
    _validate_project_does_not_exist(name)
    _store_info(create_project(name))
    echo(f'{name} created')


def _validate_project_does_not_exist(name: str) -> None:
    if _get_graph_file(name).exists():
        echo(f'{name} already exists. Ignoring...', err=True)
        raise Exit(code=1)


def _get_graph_file(name: str) -> Path:
    return _get_project_dir(name) / 'graph'


def _get_project_dir(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker' / name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _store_info(info: ProjectInfo) -> None:
    store(info.graph, _get_graph_file(info.name))
    _store_ids(info)


def _store_ids(info: ProjectInfo) -> None:
    with open(_get_project_dir(info.name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc['last_selected_choice'] = info.last_choice_id
        doc['last_id'] = info.last_generated_id
        f.write(dumps(doc))


@app.command()
def add(project_name: str) -> None:
    info = _read_project_info(project_name)
    choices = _read_choices()
    selected_choice_index = _get_selected_choice_index(len(choices))
    add_choices_and_selection(info, choices, selected_choice_index)
    _store_info(info)


def _read_project_info(name: str) -> ProjectInfo:
    return ProjectInfo(name, _get_graph(name), _get_last_selected_choice(name),
                       _get_last_id(name))


def _get_graph(name: str) -> Graph:
    try:
        graph = Graph(_get_graph_file(name))
    except FileNotFoundError:
        echo(f'Project {name} does not exist', err=True)
        raise Exit(code=1)
    return graph


def _get_last_selected_choice(name: str) -> int:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_selected_choice'])


def _get_last_id(name: str) -> int:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_id'])


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