#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Callable

import pygraphviz as pgv
from click.testing import Result
from pytest import fixture
from typer.testing import CliRunner

from route_tracker.tracker import app

CommandRunner = Callable[[], Result]


@fixture
def cli_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@fixture(autouse=True)
def test_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path
    os.environ['XDG_DATA_HOME'] = str(data_dir)
    return data_dir


@fixture
def new_command_runner(cli_runner: CliRunner) -> CommandRunner:
    return lambda: cli_runner.invoke(app, ['new', 'test_name'])




class TestNewCommand:
    @staticmethod
    def test_new_exits_normally_when_called_with_name(
            new_command_runner: CommandRunner,
    ) -> None:
        result = new_command_runner()
        assert 'test_name created' in result.stdout
        assert result.exit_code == 0

    @staticmethod
    def test_new_creates_dot_file_when_called_with_name(
            new_command_runner: CommandRunner, test_data_dir: Path,
    ) -> None:
        new_command_runner()
        assert (pgv.AGraph(test_data_dir / 'route-tracker' / 'test_name')
                == pgv.AGraph(name='test_name'))

    @staticmethod
    def test_new_exits_with_error_when_called_with_same_name_twice(
            new_command_runner: CommandRunner, test_data_dir: Path,
    ) -> None:
        new_command_runner()
        result = new_command_runner()
        assert 'test_name already exists. Ignoring...' in result.stderr
        assert result.exit_code == 1


class TestAddCommand:
    @staticmethod
    @fixture
    def add_command_runner(cli_runner: CliRunner) -> CommandRunner:
        return lambda: cli_runner.invoke(app, ['add', 'test_name'],
                                         input='choice1\n\n')

    @staticmethod
    def test_add_creates_node_when_called_with_name(
            new_command_runner: CommandRunner,
            add_command_runner: CommandRunner, test_data_dir: Path,
    ) -> None:
        new_command_runner()
        add_command_runner()

        expected = pgv.AGraph(name='test_name')
        expected.add_node('choice1', label='choice1')
        assert (pgv.AGraph(test_data_dir / 'route-tracker' / 'test_name')
                == expected)
