from typer import Option, Typer

from route_tracker.io import (ProjectContext, abort, abort_on_invalid_id,
                              draw_image, read_project_info, store_info)
from route_tracker.projects import add_ending

app = Typer()


@app.command()
def add(
        ctx: ProjectContext,
        ending_label: str = Option(..., prompt=True),
        new_choice_id: int = Option(..., prompt='Enter the id of an existing'
                                    ' choice to be selected as the current'
                                    ' choice'),
) -> None:
    project_name = ctx.obj
    info = read_project_info(project_name)
    if info.last_choice_id == 0:
        abort('You cannot add an ending directly to the start node')
    with abort_on_invalid_id():
        add_ending(info, ending_label, new_choice_id)
    store_info(info)
    draw_image(info.name, info.graph)
