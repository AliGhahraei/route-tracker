#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn, cast

from tomlkit import dumps, parse
from typer import Context, Exit, echo
from xdg import xdg_data_home

from route_tracker.graph import Graph, draw, store
from route_tracker.projects import ProjectInfo


class ProjectContext(Context):
    obj: str


def get_graph(name: str) -> Graph:
    try:
        graph = Graph(get_graph_file(name))
    except FileNotFoundError:
        abort(f'Project {name} does not exist')
    return graph


def get_graph_file(name: str) -> Path:
    return get_project_dir(name) / 'graph'


def get_project_dir(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker' / name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def abort(message: str) -> NoReturn:
    echo(message, err=True)
    raise Exit(code=1)


def draw_image(project_name: str, graph: Graph) -> None:
    draw(graph, get_image_path(project_name))


def get_image_path(project_name: str) -> Path:
    return get_project_dir(project_name) / 'routes.png'


def read_project_info(name: str) -> ProjectInfo:
    return ProjectInfo(name, get_graph(name), _get_last_selected_choice(name),
                       _get_last_id(name))


def _get_last_selected_choice(name: str) -> int:
    with open(get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_selected_choice'])


def _get_last_id(name: str) -> int:
    with open(get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_id'])


def store_info(info: ProjectInfo) -> None:
    store(info.graph, get_graph_file(info.name))
    _store_ids(info)


def _store_ids(info: ProjectInfo) -> None:
    with open(get_project_dir(info.name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc['last_selected_choice'] = info.last_choice_id
        doc['last_id'] = info.last_generated_id
        f.write(dumps(doc))
