#!/usr/bin/env python3
import sys
from contextlib import contextmanager
from typing import Generator, List

from typer import Option, Typer, echo

from route_tracker.io import (ProjectContext, abort, abort_on_invalid_id,
                              draw_image, get_project_info,
                              store_choices_and_selection, store_info)
from route_tracker.projects import (ProjectInfo, advance_to_choice,
                                    comment_choice, link_to_choice)

app = Typer()


@app.callback()
def run() -> None:
    """Add/manipulate the choices you take in your project

    Choices are represented by nodes/circles in a graph labelled by a name and
    identified by a unique number (ID). They are connected to other choices by
    arrows.
    """


@app.command()
def add(ctx: ProjectContext) -> None:
    """Add choices

    Add includes new choices in your graph. It requires you to type potential
    choices visible from your current choice and a zero-based index to
    indicate which choice you took
    (https://en.wikipedia.org/wiki/Zero-based_numbering). Can make backups as
    described in new.
    """
    info = get_project_info(ctx)
    choices = _read_choices()
    selected_choice_index = _get_selected_choice_index(len(choices))
    store_choices_and_selection(info, choices, selected_choice_index)
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


@app.command()
def advance(ctx: ProjectContext, existing_id: int = Option(..., prompt=True)) \
        -> None:
    """Advance to another existing choice

    Advance allows you to "jump" from your current choice to any other choice
    in your graph. Can make backups as described in new.
    """
    info = get_project_info(ctx)
    with _abort_on_invalid_or_current_id('advance', existing_id, info):
        advance_to_choice(info, existing_id)
    store_info(info)
    draw_image(info.name, info.graph)


@contextmanager
def _abort_on_invalid_or_current_id(routine_name: str, node_id: int,
                                    info: ProjectInfo) \
        -> Generator[None, None, None]:
    if node_id == info.last_choice_id:
        abort(f'Cannot {routine_name} currently selected node to itself')
    with abort_on_invalid_id():
        yield


@app.command()
def link(ctx: ProjectContext, existing_id: int = Option(..., prompt=True)) \
        -> None:
    """Link to another existing choice

    Link allows you to draw an arrow from your current choice to any other
    choice in your graph. It does not mark the target choice as selected.
    """
    info = get_project_info(ctx)
    with _abort_on_invalid_or_current_id('link', existing_id, info):
        link_to_choice(info, existing_id)
    store_info(info)
    draw_image(info.name, info.graph)


@app.command()
def comment(ctx: ProjectContext, existing_id: int = Option(..., prompt=True),
            comment_text: str = Option(..., prompt=True)) -> None:
    """Add a comment to an existing choice

    Comment displays a message next to a choice.
    """
    info = get_project_info(ctx)
    with abort_on_invalid_id():
        comment_choice(info, existing_id, comment_text)
    store_info(info)
    draw_image(info.name, info.graph)
