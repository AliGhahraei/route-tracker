#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, cast

import pygraphviz as pgv
from tomlkit import dumps, parse
from typer import Exit, Typer, echo
from xdg import xdg_data_home

app = Typer()


@app.command()
def new(name: str) -> None:
    if _get_graph_file(name).exists():
        echo(f'{name} already exists. Ignoring...', err=True)
        raise Exit(code=1)
    _create_new_graph(name)
    _store_last_selected_choice(name, 'start')


def _get_graph_file(name: str) -> Path:
    return _get_project_dir(name) / 'graph'


def _get_project_dir(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker' / name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _create_new_graph(name: str) -> None:
    graph = pgv.AGraph(name=name)
    graph.add_node('start', label='start')
    graph.write(_get_graph_file(name))
    echo(f'{name} created')


def _store_last_selected_choice(project_name: str, choice: str) -> None:
    with open(_get_project_dir(project_name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc['last_selected_choice'] = choice
        f.write(dumps(doc))


@app.command()
def add(project_name: str) -> None:
    _get_graph(project_name)
    choices = _read_choices()
    selected_choice = _get_selected_choice(choices)
    graph = _add_choices_to_graph(choices, project_name)
    graph.write(_get_graph_file(project_name))
    _store_last_selected_choice(project_name, selected_choice)


def _get_graph(name: str) -> pgv.AGraph:
    try:
        graph = pgv.AGraph(_get_graph_file(name))
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


def _get_selected_choice(choices: Sequence[str]) -> str:
    index_input = input('Enter the zero-based index of your selection\n')
    try:
        selected_choice = choices[int(index_input)]
    except ValueError:
        echo(f'Index {index_input} is not a number', err=True)
        raise Exit(code=1)
    except IndexError:
        echo(f'Index {index_input} is out of bounds', err=True)
        raise Exit(code=1)
    return selected_choice


def _add_choices_to_graph(choices: Iterable[str], project_name: str) \
        -> pgv.AGraph:
    graph = _get_graph(project_name)
    last_selected_choice = _get_last_selected_choice(project_name)
    for choice in choices:
        graph.add_node(choice, label=choice)
        graph.add_edge(last_selected_choice, choice)
    return graph


def _get_last_selected_choice(name: str) -> str:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(str, config['last_selected_choice'])
