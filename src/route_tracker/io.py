#!/usr/bin/env python3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from typing import (Any, Dict, Generator, MutableMapping, NoReturn, Optional,
                    Sequence, cast)

from tomlkit import dumps, parse
from typer import Context, Exit, echo
from xdg import xdg_data_home

from route_tracker.graph import Graph, InvalidNodeId, draw, store
from route_tracker.projects import (ProjectInfo, SaveFileInfo,
                                    add_choices_and_selection, add_ending,
                                    create_project)

_LAST_CHOICE_ID = 'last_choice_id'
_LAST_GENERATED_ID = 'last_generated_id'
_NEXT_NUMERIC_ENDING_ID = 'next_numeric_ending_id'
_ROUTE_ID = 'route_id'
TARGET_DIRECTORY = 'target_directory'
FILE = 'file'
_IDS = (
    _LAST_CHOICE_ID,
    _LAST_GENERATED_ID,
    _NEXT_NUMERIC_ENDING_ID,
    _ROUTE_ID,
)


class NewContext(Context):
    obj: str


class ProjectContext(Context):
    obj: 'ContextObject'


@dataclass
class ContextObject:
    info: ProjectInfo


def copy_save_file(save: bool, info: SaveFileInfo, past_selection: int) \
        -> None:
    if save and info.file and info.target_directory:
        info.target_directory.mkdir(parents=True, exist_ok=True)
        copy2(
            info.file,
            info.target_directory / f'{past_selection}_{info.route_id}',
        )


def get_project_info(ctx: ProjectContext) -> ProjectInfo:
    return ctx.obj.info


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
    return ProjectInfo(name, get_graph(name), **_get_metadata(name))


def _get_metadata(name: str) -> Dict[str, Any]:
    with open(get_project_dir(name) / 'data') as f:
        config = cast(MutableMapping[str, Any], parse(f.read()))
    metadata = {key: config[key] for key in _IDS}
    try:
        file = Path(config[FILE])
        target_directory = Path(config[TARGET_DIRECTORY])
    except KeyError:
        pass
    else:
        metadata.update(file=file, target_directory=target_directory)
    return metadata


def store_info(info: ProjectInfo) -> None:
    store(info.graph, get_graph_file(info.name))
    _store_metadata(info)


def _store_metadata(info: ProjectInfo) -> None:
    with open(get_project_dir(info.name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc.update(dict(zip(_IDS, [
            info.last_choice_id,
            info.last_generated_id,
            info.next_numeric_ending_id,
            info.route_id
        ])))
        if info.file:
            doc[FILE] = str(info.file)
            doc[TARGET_DIRECTORY] = str(info.target_directory)
        f.write(dumps(doc))


def store_new_project(name: str, file: Optional[Path] = None,
                      target_directory: Optional[Path] = None) -> ProjectInfo:
    info = create_project(name, file, target_directory)
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
