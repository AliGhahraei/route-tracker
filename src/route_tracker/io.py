#!/usr/bin/env python3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Mapping, NoReturn, Sequence, Tuple, cast

from tomlkit import dumps, parse
from typer import Context, Exit, echo
from xdg import xdg_data_home

from route_tracker.graph import Graph, InvalidNodeId, draw, store
from route_tracker.projects import (ProjectInfo, add_choices_and_selection,
                                    add_ending, create_project)

LAST_CHOICE_ID = 'last_choice_id'
LAST_GENERATED_ID = 'last_generated_id'
NEXT_NUMERIC_ENDING_ID = 'next_numeric_ending_id'
ROUTE_ID = 'route_id'


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


@contextmanager
def abort_on_invalid_id() -> Generator[None, None, None]:
    try:
        yield
    except InvalidNodeId as e:
        abort(f'id {e.node_id} does not exist')


def read_project_info(name: str) -> ProjectInfo:
    return ProjectInfo(name, get_graph(name), *_get_ids(name))


def _get_ids(name: str) -> Tuple[int, int, int, int]:
    with open(get_project_dir(name) / 'data') as f:
        config = cast(Mapping[str, int], parse(f.read()))
        return (config[LAST_CHOICE_ID], config[LAST_GENERATED_ID],
                config[NEXT_NUMERIC_ENDING_ID], config[ROUTE_ID])


def store_info(info: ProjectInfo) -> None:
    store(info.graph, get_graph_file(info.name))
    _store_ids(info)


def _store_ids(info: ProjectInfo) -> None:
    with open(get_project_dir(info.name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc[LAST_CHOICE_ID] = info.last_choice_id
        doc[LAST_GENERATED_ID] = info.last_generated_id
        doc[NEXT_NUMERIC_ENDING_ID] = info.next_numeric_ending_id
        doc[ROUTE_ID] = info.route_id
        f.write(dumps(doc))


def store_new_project(name: str) -> ProjectInfo:
    info = create_project(name)
    store_info(info)
    return info


def store_choices_and_selection(info: ProjectInfo, choices: Sequence[str],
                                selected_choice_index: int) -> None:
    add_choices_and_selection(info, choices, selected_choice_index)
    store_info(info)


def store_ending(info: ProjectInfo, ending_label: str, new_choice_id: int) \
        -> None:
    with abort_on_invalid_id():
        add_ending(info, ending_label, new_choice_id)
    store_info(info)
