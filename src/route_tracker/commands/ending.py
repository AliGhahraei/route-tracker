from typer import Option, Typer

from route_tracker.io import (ProjectContext, abort_on_invalid_id, draw_image,
                              read_project_info, store_ending, store_info)
from route_tracker.projects import link_to_ending

CHOICE_PROMPT = ('Enter the id of an existing choice to be selected as the'
                 ' current choice')

app = Typer()


@app.callback()
def run() -> None:
    """Add/manipulates route/path endings

    Endings are black circles in the graph with a name and ID (which always
    starts with "E"). They mark the end of a route or a succession of choices.
    Whenever you add one, you will also have to specify an existing choice to
    "jump" to because you cannot select an ending and therefore you cannot
    advance to it.
    """


@app.command()
def add(
        ctx: ProjectContext,
        ending_label: str = Option(..., prompt=True),
        new_choice_id: int = Option(..., prompt=CHOICE_PROMPT),
) -> None:
    """Add an ending

    Add creates an ending and links your choice to it. It then jumps to the
    specified new choice and starts a new route
    """
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
    """Link to an existing ending

    Link draws an arrow from your current choice to the specified ending. It
    then jumps to the specified new choice and starts a new route.
    """
    project_name = ctx.obj
    info = read_project_info(project_name)
    with abort_on_invalid_id():
        link_to_ending(info, ending_id, new_choice_id)
    store_info(info)
    draw_image(info.name, info.graph)
