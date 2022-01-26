#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Callable, Protocol

import pygraphviz as pgv
from click.testing import Result
from pytest import fixture, mark
from typer.testing import CliRunner

from route_tracker.tracker import app

AddRunner = Callable[[str], Result]


class NewRunner(Protocol):
    def __call__(self, project_name: str = ...) -> Result:
        pass


@fixture
def cli_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@fixture(autouse=True)
def test_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path
    os.environ['XDG_DATA_HOME'] = str(data_dir)
    return data_dir


@fixture
def new_runner(cli_runner: CliRunner) -> NewRunner:
    def runner(project_name: str = 'test_name') -> Result:
        return cli_runner.invoke(app, ['new', project_name])
    return runner


@fixture
def starting_graph() -> pgv.AGraph:
    graph = pgv.AGraph(name='test_name')
    graph.add_node('start', label='start')
    return graph


def assert_graphs_equal(data_dir: Path, expected_graph: pgv.AGraph) -> None:
    graph = pgv.AGraph(data_dir / 'route-tracker' / 'test_name' / 'graph')
    assert graph.to_string() == expected_graph.to_string()


def assert_normal_exit(result: Result, message: str) -> None:
    assert message in result.stdout
    assert result.exit_code == 0


def assert_error_exit(result: Result, message: str) -> None:
    assert message in result.stderr
    assert result.exit_code == 1


class TestNewCommand:
    @staticmethod
    def test_new_exits_normally_when_called_with_name(
            new_runner: NewRunner,
    ) -> None:
        assert_normal_exit(new_runner(), 'test_name created')

    @staticmethod
    def test_new_creates_dot_file_when_called_with_name(
            new_runner: NewRunner, test_data_dir: Path,
            starting_graph: pgv.AGraph,
    ) -> None:
        new_runner()
        assert_graphs_equal(test_data_dir, starting_graph)

    @staticmethod
    def test_new_exits_with_error_when_called_with_same_name_twice(
            new_runner: NewRunner, test_data_dir: Path,
    ) -> None:
        new_runner()
        assert_error_exit(new_runner(),
                          'test_name already exists. Ignoring...')

    @staticmethod
    def test_new_exits_normally_when_called_with_different_names(
            new_runner: NewRunner,
    ) -> None:
        assert_normal_exit(new_runner(), 'test_name created')
        assert_normal_exit(new_runner('another_name'), 'another_name created')


class TestAddCommand:
    @staticmethod
    @fixture
    def add_runner(cli_runner: CliRunner) -> AddRunner:
        return lambda input_: cli_runner.invoke(app, ['add', 'test_name'],
                                                input=input_)

    @staticmethod
    def test_add_exits_normally_when_called_with_choices(
            new_runner: NewRunner, add_runner: AddRunner,
    ) -> None:
        new_runner()
        assert_normal_exit(add_runner('choice1\n\n0'),
                           'Enter available choices separated by newlines. A'
                           ' blank line ends the input\nEnter the zero-based'
                           ' index of your selection')

    @staticmethod
    def test_add_saves_single_choice_when_called_with_single_choice(
            new_runner: NewRunner, starting_graph: pgv.AGraph,
            add_runner: AddRunner, test_data_dir: Path,
    ) -> None:
        new_runner()
        add_runner('choice1\n\n0')

        expected = starting_graph
        expected.add_node('choice1', label='choice1')
        expected.add_edge('start', 'choice1')
        assert_graphs_equal(test_data_dir, expected)

    @staticmethod
    def test_add_saves_choices_when_called_with_multiple_choices(
            new_runner: NewRunner, starting_graph: pgv.AGraph,
            add_runner: AddRunner, test_data_dir: Path,
    ) -> None:
        new_runner()
        add_runner('choice1\nchoice2\n\n1')

        expected = starting_graph
        expected.add_node('choice1', label='choice1')
        expected.add_edge('start', 'choice1')
        expected.add_node('choice2', label='choice2')
        expected.add_edge('start', 'choice2')
        assert_graphs_equal(test_data_dir, expected)

    @staticmethod
    def test_add_saves_choices_when_called_with_multiple_add_commands(
            new_runner: NewRunner, starting_graph: pgv.AGraph,
            add_runner: AddRunner, test_data_dir: Path,
    ) -> None:
        new_runner()
        add_runner('choice1\n\n0')
        add_runner('choice2\n\n0')

        expected = starting_graph
        expected.add_node('choice1', label='choice1')
        expected.add_edge('start', 'choice1')
        expected.add_node('choice2', label='choice2')
        expected.add_edge('choice1', 'choice2')
        assert_graphs_equal(test_data_dir, expected)

    @staticmethod
    def test_add_exits_with_error_when_called_with_no_choices(
            new_runner: NewRunner, add_runner: AddRunner,
    ) -> None:
        new_runner()
        assert_error_exit(add_runner('\n'),
                          'At least one choice must be entered')

    @staticmethod
    @mark.parametrize('index', [1, 2, -2])
    def test_add_exits_with_error_when_selected_choice_is_out_of_bounds(
            index: int, new_runner: NewRunner, add_runner: AddRunner,
    ) -> None:
        new_runner()
        assert_error_exit(add_runner(f'choice1\n\n{index}'),
                          f'Index {index} is out of bounds')

    @staticmethod
    def test_add_exits_with_error_when_selected_choice_is_not_a_number(
            new_runner: NewRunner, add_runner: AddRunner,
    ) -> None:
        new_runner()
        assert_error_exit(add_runner('choice1\n\nnot_a_number'),
                          'Index not_a_number is not a number')

    @staticmethod
    def test_add_aborts_if_project_does_not_exist(
            add_runner: AddRunner,
    ) -> None:
        assert_error_exit(add_runner('choice\n\n'),
                          'Project test_name does not exist')
