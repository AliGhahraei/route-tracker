#!/usr/bin/env python3
import sys
from typing import List

from typer import Typer, echo

from route_tracker.io import (ProjectContext, abort, draw_image,
                              read_project_info, store_info)
from route_tracker.projects import add_choices_and_selection

app = Typer()


@app.command()
def add(ctx: ProjectContext) -> None:
    project_name = ctx.obj
    info = read_project_info(project_name)
    choices = _read_choices()
    selected_choice_index = _get_selected_choice_index(len(choices))
    add_choices_and_selection(info, choices, selected_choice_index)
    store_info(info)
    draw_image(info.name, info.graph)


def _read_choices() -> List[str]:
    echo('Enter available choices separated by newlines. A blank line ends the'
         ' input')
    choices: List[str] = []
    while (line := sys.stdin.readline()) != '\n':
        choices.append(line.rstrip())
    if not choices:
        abort('At least one choice must be entered')
    return choices


def _get_selected_choice_index(choices_number: int) -> int:
    index_input = input('Enter the zero-based index of your selection\n')
    try:
        index = int(index_input)
    except ValueError:
        abort(f'Index {index_input} is not a number')
    if index < 0 or index >= choices_number:
        abort(f'Index {index} is out of bounds')
    return index
