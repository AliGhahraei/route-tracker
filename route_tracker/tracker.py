#!/usr/bin/env python3
from typer import Typer, echo

app = Typer()


@app.command()
def new(name: str) -> None:
    echo(f'{name} created')
