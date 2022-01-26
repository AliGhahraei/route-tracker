#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List, Sequence, Tuple, cast

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
    _store_choice_info(name, 0, 0)


def _get_graph_file(name: str) -> Path:
    return _get_project_dir(name) / 'graph'


def _get_project_dir(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker' / name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _create_new_graph(name: str) -> None:
    graph = pgv.AGraph(name=name, directed=True)
    graph.add_node(0, label='start')
    graph.write(_get_graph_file(name))
    echo(f'{name} created')


def _store_choice_info(project_name: str, last_choice: int, last_id: int) \
        -> None:
    with open(_get_project_dir(project_name) / 'data', 'w+') as f:
        doc = parse(f.read())
        doc['last_selected_choice'] = last_choice
        doc['last_id'] = last_choice
        f.write(dumps(doc))


@app.command()
def add(project_name: str) -> None:
    _get_graph(project_name)
    choices = _read_choices()
    graph, choices_ids = _add_choices_to_graph(choices, project_name)
    selected_choice = _get_selected_choice(choices_ids)
    graph.write(_get_graph_file(project_name))
    _store_choice_info(project_name, selected_choice, choices_ids[-1])


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


def _get_selected_choice(choices: Sequence[int]) -> int:
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


def _add_choices_to_graph(choices: Sequence[str], project_name: str) \
        -> Tuple[pgv.AGraph, Sequence[int]]:
    next_id = _get_last_id(project_name) + 1
    choices_ids = list(range(next_id, next_id + len(choices)))
    graph = _get_graph(project_name)
    last_selected_choice = _get_last_selected_choice(project_name)
    for choice_label, choice_id in zip(choices, choices_ids):
        graph.add_node(choice_id, label=choice_label)
        graph.add_edge(last_selected_choice, choice_id)
    return graph, choices_ids


def _get_last_id(name: str) -> int:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(int, config['last_id'])


def _get_last_selected_choice(name: str) -> str:
    with open(_get_project_dir(name) / 'data') as f:
        config = parse(f.read())
        return cast(str, config['last_selected_choice'])
