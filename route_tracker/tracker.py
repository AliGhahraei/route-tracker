#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List

from pydot import Dot, Node, graph_from_dot_file
from typer import Exit, Typer, echo
from xdg import xdg_data_home

app = Typer()


@app.command()
def new(name: str) -> None:
    data_file = get_data_file(name)
    if data_file.exists():
        echo(f'{name} already exists. Ignoring...', err=True)
        raise Exit(code=1)
    Dot(name, graph_type='graph').write_dot(data_file)
    echo(f'{name} created')


@app.command()
def add(project_name: str) -> None:
    choices: List[str] = []
    while (line := sys.stdin.readline()) != '\n':
        choices.append(line.rstrip())

    data_file = get_data_file(project_name)
    graph = graph_from_dot_file(data_file)[0]
    for choice in choices:
        graph.add_node(Node(choice, label=choice))
    graph.write_dot(data_file)


def get_data_file(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker'
    data_dir.mkdir(exist_ok=True)
    return data_dir / name
