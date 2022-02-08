#!/usr/bin/env python3
from pathlib import Path
from subprocess import Popen
from typing import MutableMapping, Optional

from tomlkit import document, dumps, parse
from typer import Context, Option, Typer, echo
from xdg import xdg_config_home

from route_tracker.commands.choices import app as choices_app
from route_tracker.commands.ending import app as ending_app
from route_tracker.io import (ContextObject, ProjectContext, abort, draw_image,
                              get_graph, get_graph_file, get_image_path,
                              get_name, store_new_project)

app = Typer()
app.add_typer(choices_app, name='choices')
app.add_typer(ending_app, name='ending')


@app.callback(context_settings={'obj': {}})
def run(ctx: Context, project_name: str) -> None:
    """Keep track of your choices

    Route-tracker helps you keep track of your choices when playing a
    text-based game, when reading a visual novel or any time you want to track
    some kind of decision-making process. Each individual "thing" tracked by it
    is called a project. It can show a visualization of the choices you have
    selected. The current choice is shown with a double circle around it.
    """
    ctx.obj = ContextObject(project_name, **ctx.obj)


@app.command()
def new(ctx: ProjectContext, save_file: Optional[Path] = Option(None),
        target_directory: Optional[Path] = Option(None)) -> None:
    """Creates a new project

    Each program or "thing" you want to track should have its own project.
    If save_file and target_directory are passed, a backup of save_file will
    be stored in target_directory when you call choices advance or choices add
    with the file name <selected_node_id>.<route_id>.
    """
    name = get_name(ctx)
    _validate_project_does_not_exist(name)
    if bool(save_file) ^ bool(target_directory):
        abort('save_file and test_directory must be passed together')

    args = ((Path(save_file), Path(target_directory))
            if save_file and target_directory else ())
    info = store_new_project(name, *args)
    echo(f'{name} created')
    draw_image(info.name, info.graph)


def _validate_project_does_not_exist(name: str) -> None:
    if get_graph_file(name).exists():
        abort(f'{name} already exists. Ignoring...')


@app.command()
def view(ctx: ProjectContext) -> None:
    """Visualize your project

    View asks you for an image viewer command if you have not configured one
    before (it must handle PNGs) and displays your project as a graph
    """
    project_name = get_name(ctx)
    draw_image(project_name, get_graph(project_name))
    Popen([_get_viewer(), get_image_path(project_name)])


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
