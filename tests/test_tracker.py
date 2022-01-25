#!/usr/bin/env python3
from pytest import fixture
from typer.testing import CliRunner

from route_tracker.tracker import app


@fixture
def runner() -> CliRunner:
    return CliRunner()


class TestNewCommand:
    @staticmethod
    def test_new_exits_normally_when_called_with_name(runner: CliRunner) \
            -> None:
        assert runner.invoke(app, ['test_name']).exit_code == 0

    @staticmethod
    def test_new_shows_project_created_when_called_with_name(
            runner: CliRunner,
    ) -> None:
        assert 'test_name created' in runner.invoke(app, ['test_name']).stdout
