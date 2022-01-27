#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Callable, Generator, Protocol
from unittest.mock import Mock, patch

import pygraphviz as pgv
from click.testing import Result
from pytest import fixture, mark
from typer.testing import CliRunner

from route_tracker.tracker import app

AddRunner = Callable[[str], Result]


class NewRunner(Protocol):
    def __call__(self, project_name: str = ...) -> Result:
        pass


class ViewRunner(Protocol):
    def __call__(self, project_name: str = ..., input_: str = ...) -> Result:
        pass


@fixture
def cli_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@fixture(autouse=True)
def test_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path
    os.environ['XDG_DATA_HOME'] = str(data_dir)
    return data_dir


@fixture(autouse=True)
def test_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path
    os.environ['XDG_CONFIG_HOME'] = str(config_dir)
    return config_dir


@fixture(autouse=True)
def mock_run() -> Generator[Mock, None, None]:
    with patch('route_tracker.tracker.run') as mock:
        yield mock


@fixture
def new_runner(cli_runner: CliRunner) -> NewRunner:
    def runner(project_name: str = 'test_name') -> Result:
        return cli_runner.invoke(app, ['new', project_name])
    return runner


@fixture
def starting_graph() -> pgv.AGraph:
    graph = pgv.AGraph(name='test_name', directed=True)
    graph.add_node(0, label='start')
    return graph


def get_project_dir(data_dir: Path) -> Path:
    return data_dir / 'route-tracker' / 'test_name'


def assert_graphs_equal(data_dir: Path, expected_graph: pgv.AGraph) -> None:
    graph = pgv.AGraph(get_project_dir(data_dir) / 'graph')
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
        expected.add_node(1, label='choice1')
        expected.add_edge(0, 1, color='green')
        assert_graphs_equal(test_data_dir, expected)

    @staticmethod
    def test_add_saves_choices_when_called_with_multiple_choices(
            new_runner: NewRunner, starting_graph: pgv.AGraph,
            add_runner: AddRunner, test_data_dir: Path,
    ) -> None:
        new_runner()
        add_runner('choice1\nchoice2\n\n1')

        expected = starting_graph
        expected.add_node(1, label='choice1')
        expected.add_edge(0, 1)
        expected.add_node(2, label='choice2')
        expected.add_edge(0, 2, color='green')
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
        expected.add_node(1, label='choice1')
        expected.add_edge(0, 1, color='green')
        expected.add_node(2, label='choice2')
        expected.add_edge(1, 2, color='green')
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


class TestViewCommand:
    @staticmethod
    @fixture
    def view_runner(cli_runner: CliRunner) -> ViewRunner:
        def runner(project_name: str = 'test_name', input_: str = '') \
                -> Result:
            return cli_runner.invoke(app, ['view', project_name], input=input_)
        return runner

    @staticmethod
    def test_view_prompts_for_viewer_if_not_configured(
            new_runner: NewRunner, view_runner: ViewRunner,
    ) -> None:
        new_runner()
        assert_normal_exit(view_runner(input_='test_viewer\n'),
                           'Image viewer command:')

    @staticmethod
    def test_view_does_not_prompt_for_viewer_if_configured(
            new_runner: NewRunner, view_runner: ViewRunner,
    ) -> None:
        new_runner()
        view_runner(input_='test_viewer\n')
        assert_normal_exit(view_runner(), '')

    @staticmethod
    def test_view_shows_existing_graph(
            new_runner: NewRunner, view_runner: ViewRunner,
            test_data_dir: Path, mock_run: Mock,
    ) -> None:
        new_runner()
        view_runner(input_='test_viewer\n')

        routes = get_project_dir(test_data_dir) / 'routes.png'
        assert routes.exists()
        mock_run.assert_called_once_with(
            ['test_viewer', routes],
        )

    @staticmethod
    def test_view_exits_with_error_if_project_does_not_exist(
            view_runner: ViewRunner,
    ) -> None:
        assert_error_exit(view_runner(), 'Project test_name does not exist')
