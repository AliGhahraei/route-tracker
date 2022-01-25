#!/usr/bin/env python3
from pydot import Dot
from typer import Typer, echo
from xdg import xdg_data_home

app = Typer()


@app.command()
def new(name: str) -> None:
    data_dir = xdg_data_home() / 'route-tracker'
    data_dir.mkdir(exist_ok=True)
    Dot(name, graph_type='graph').write_dot(data_dir / name)
    echo(f'{name} created')
