#!/usr/bin/env python3
import sys
from pathlib import Path
from subprocess import Popen
from typing import List, MutableMapping, NoReturn, Tuple, cast

from tomlkit import document, dumps, parse
from typer import Context, Exit, Typer, echo
from xdg import xdg_config_home, xdg_data_home

from route_tracker.graph import Graph, InvalidNodeId, draw, store
from route_tracker.projects import (ProjectInfo, add_choices_and_selection,
                                    add_ending, create_project)

app = Typer()


class ProjectContext(Context):
    obj: str


@app.callback()
def run(ctx: Context, project_name: str) -> None:
    ctx.obj = project_name


@app.command()
def new(ctx: ProjectContext) -> None:
    name = ctx.obj
    _validate_project_does_not_exist(name)
    info = create_project(name)
    _store_info(info)
    echo(f'{name} created')
    _draw_image(info.name, info.graph)


def _validate_project_does_not_exist(name: str) -> None:
    if _get_graph_file(name).exists():
        _abort(f'{name} already exists. Ignoring...')


def _abort(message: str) -> NoReturn:
    echo(message, err=True)
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


def _draw_image(project_name: str, graph: Graph) -> None:
    draw(graph, _get_image_path(project_name))


def _get_image_path(project_name: str) -> Path:
    return _get_project_dir(project_name) / 'routes.png'


@app.command()
def choices(ctx: ProjectContext) -> None:
    project_name = ctx.obj
    info = _read_project_info(project_name)
    choices = _read_choices()
    selected_choice_index = _get_selected_choice_index(len(choices))
    add_choices_and_selection(info, choices, selected_choice_index)
    _store_info(info)
    _draw_image(info.name, info.graph)


def _read_project_info(name: str) -> ProjectInfo:
    return ProjectInfo(name, _get_graph(name), _get_last_selected_choice(name),
                       _get_last_id(name))


def _get_graph(name: str) -> Graph:
    try:
        graph = Graph(_get_graph_file(name))
    except FileNotFoundError:
        _abort(f'Project {name} does not exist')
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
        _abort('At least one choice must be entered')
    return choices


def _get_selected_choice_index(choices_number: int) -> int:
    index_input = input('Enter the zero-based index of your selection\n')
    try:
        index = int(index_input)
    except ValueError:
        _abort(f'Index {index_input} is not a number')
    if index < 0 or index >= choices_number:
        _abort(f'Index {index} is out of bounds')
    return index


@app.command()
def ending(ctx: ProjectContext) -> None:
    project_name = ctx.obj
    info = _read_project_info(project_name)
    if info.last_choice_id == 0:
        _abort('You cannot add an ending directly to the start node')
    _add_ending(info)
    _store_info(info)
    _draw_image(info.name, info.graph)


def _add_ending(info: ProjectInfo) -> None:
    ending_label, new_choice_id = _read_ending_info()
    try:
        add_ending(info, ending_label, new_choice_id)
    except InvalidNodeId:
        _abort(f'id {new_choice_id} does not exist')


def _read_ending_info() -> Tuple[str, int]:
    ending_label = input("Enter the ending's label\n")
    new_choice_input = input('Enter the id of an existing choice to be'
                             ' selected as the current choice\n')
    try:
        new_choice_id = int(new_choice_input)
    except ValueError:
        _abort('The id must be an integer')
    return ending_label, new_choice_id


@app.command()
def view(ctx: ProjectContext) -> None:
    project_name = ctx.obj
    _draw_image(project_name, _get_graph(project_name))
    Popen([_get_viewer(), _get_image_path(project_name)])


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
