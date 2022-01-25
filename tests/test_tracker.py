#!/usr/bin/env python3
import os
from pathlib import Path
from textwrap import dedent
from typing import Callable

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


class TestNewCommand:
    @staticmethod
    @fixture
    def command_runner(cli_runner: CliRunner) -> CommandRunner:
        return lambda: cli_runner.invoke(app, ['test_name'])

    @staticmethod
    def test_new_exits_normally_when_called_with_name(
            command_runner: CommandRunner,
    ) -> None:
        result = command_runner()
        assert 'test_name created' in result.stdout
        assert result.exit_code == 0

    @staticmethod
    def test_new_creates_dot_file_when_called_with_name(
            command_runner: CommandRunner, test_data_dir: Path,
    ) -> None:
        command_runner()
        with open(test_data_dir / 'route-tracker' / 'test_name') as f:
            expected = dedent("""\
            graph test_name {
            \tgraph [bb="0,0,0,0"];
            \tnode [label="\\N"];
            }
            """)
            assert f.read() == expected

    @staticmethod
    def test_new_exits_with_error_when_called_with_same_name_twice(
            command_runner: CommandRunner, test_data_dir: Path,
    ) -> None:
        command_runner()
        result = command_runner()
        assert 'test_name already exists. Ignoring...' in result.stderr
        assert result.exit_code == 1
