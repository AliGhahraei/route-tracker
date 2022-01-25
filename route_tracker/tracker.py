#!/usr/bin/env python3
from pydot import Dot
from typer import Exit, Typer, echo
from xdg import xdg_data_home

app = Typer()


@app.command()
def new(name: str) -> None:
    data_dir = xdg_data_home() / 'route-tracker'
    data_dir.mkdir(exist_ok=True)
    data_file = data_dir / name
    if data_file.exists():
        echo(f'{name} already exists. Ignoring...', err=True)
        raise Exit(code=1)
    Dot(name, graph_type='graph').write_dot(data_file)
    echo(f'{name} created')
