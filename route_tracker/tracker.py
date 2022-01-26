#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List

import pygraphviz as pgv
from typer import Exit, Typer, echo
from xdg import xdg_data_home

app = Typer()


@app.command()
def new(name: str) -> None:
    data_file = get_data_file(name)
    if data_file.exists():
        echo(f'{name} already exists. Ignoring...', err=True)
        raise Exit(code=1)
    pgv.AGraph(name=name).write(data_file)
    echo(f'{name} created')


@app.command()
def add(project_name: str) -> None:
    choices: List[str] = []
    while (line := sys.stdin.readline()) != '\n':
        choices.append(line.rstrip())

    data_file = get_data_file(project_name)
    graph = pgv.AGraph(data_file)
    for choice in choices:
        graph.add_node(choice, label=choice)
    graph.write(data_file)


def get_data_file(name: str) -> Path:
    data_dir = xdg_data_home() / 'route-tracker'
    data_dir.mkdir(exist_ok=True)
    return data_dir / name
