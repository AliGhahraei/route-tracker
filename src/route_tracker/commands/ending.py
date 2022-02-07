from typer import Option, Typer

from route_tracker.io import (ProjectContext, abort_on_invalid_id, draw_image,
                              read_project_info, store_ending, store_info)
from route_tracker.projects import link_to_ending

CHOICE_PROMPT = ('Enter the id of an existing choice to be selected as the'
                 ' current choice')

app = Typer()


@app.command()
def add(
        ctx: ProjectContext,
        ending_label: str = Option(..., prompt=True),
        new_choice_id: int = Option(..., prompt=CHOICE_PROMPT),
) -> None:
    project_name = ctx.obj
    info = read_project_info(project_name)
    store_ending(info, ending_label, new_choice_id)
    draw_image(info.name, info.graph)


@app.command()
def link(
        ctx: ProjectContext,
        ending_id: str = Option(..., prompt='Enter an ending id including the'
                                            ' "E"'),
        new_choice_id: int = Option(..., prompt=CHOICE_PROMPT),
) -> None:
    project_name = ctx.obj
    info = read_project_info(project_name)
    with abort_on_invalid_id():
        link_to_ending(info, ending_id, new_choice_id)
    store_info(info)
    draw_image(info.name, info.graph)
