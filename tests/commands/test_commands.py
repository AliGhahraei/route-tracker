#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Callable, Generator, Optional, Protocol
from unittest.mock import ANY, Mock, call, patch

from click.testing import Result
from pytest import FixtureRequest, fixture, mark
from typer.testing import CliRunner

from route_tracker.commands import app
from route_tracker.graph import (Graph, add_edge, add_ending_node, add_node,
                                 add_selected_node)

InputRunner = Callable[[str], Result]


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
def mock_spawn() -> Generator[Mock, None, None]:
    with patch('route_tracker.commands.Popen') as mock:
        yield mock


@fixture(autouse=True)
def mock_draw(request: FixtureRequest) \
        -> Generator[Optional[Mock], None, None]:
    if 'skip_mock_draw_autouse' in request.keywords:
        yield None
    else:
        with patch('route_tracker.commands.draw') as mock:
            yield mock


@fixture
def new_runner(cli_runner: CliRunner) -> NewRunner:
    def runner(project_name: str = 'test_name') -> Result:
        return cli_runner.invoke(app, [project_name, 'new'])
    return runner


@fixture
def choices_runner(cli_runner: CliRunner) -> InputRunner:
    return lambda input_: cli_runner.invoke(app, ['test_name', 'choices'],
                                            input=input_)


def get_project_dir(data_dir: Path) -> Path:
    return data_dir / 'route-tracker' / 'test_name'


def get_image_dir(data_dir: Path) -> Path:
    return get_project_dir(data_dir) / 'routes.png'


def assert_stored_graph_equals(data_dir: Path, expected_graph: Graph) -> None:
    graph = Graph(get_project_dir(data_dir) / 'graph')
    assert graph.content == expected_graph.content


def assert_draw_called(mock_draw: Mock, data_dir: Path, *,
                       expected_calls: int = 1) -> None:
    assert expected_calls == len(mock_draw.mock_calls)
    mock_draw.assert_has_calls(
        [call(ANY, get_image_dir(data_dir))] * expected_calls,
    )


def assert_normal_exit(result: Result, message: str) -> None:
    assert message in result.stdout
    assert result.exit_code == 0


def assert_error_exit(result: Result, message: str) -> None:
    assert message in result.stderr
    assert result.exit_code == 1


class TestNewCommand:
    @staticmethod
    def test_new_exits_with_correct_message_when_called_with_name(
            new_runner: NewRunner,
    ) -> None:
        assert_normal_exit(new_runner(), 'test_name created')

    @staticmethod
    def test_new_creates_dot_file_when_called_with_name(
            new_runner: NewRunner, test_data_dir: Path, empty_graph: Graph,
    ) -> None:
        new_runner()

        expected_graph = empty_graph
        add_selected_node(expected_graph, 0, '0. start')
        assert_stored_graph_equals(test_data_dir, expected_graph)

    @staticmethod
    def test_new_exits_with_error_when_called_with_same_name_twice(
            new_runner: NewRunner, test_data_dir: Path,
    ) -> None:
        new_runner()
        assert_error_exit(new_runner(),
                          'test_name already exists. Ignoring...')

    @staticmethod
    def test_new_exits_with_correct_messages_when_called_with_different_names(
            new_runner: NewRunner,
    ) -> None:
        assert_normal_exit(new_runner(), 'test_name created')
        assert_normal_exit(new_runner('another_name'), 'another_name created')

    @staticmethod
    def test_new_draws_graph(
            new_runner: NewRunner, test_data_dir: Path, mock_draw: Mock,
    ) -> None:
        new_runner()
        assert_draw_called(mock_draw, test_data_dir)


class TestChoicesCommand:
    @staticmethod
    def test_choices_exits_with_correct_messages_when_called_with_choices(
            new_runner: NewRunner, choices_runner: InputRunner,
    ) -> None:
        new_runner()
        assert_normal_exit(choices_runner('choice1\n\n0'),
                           'Enter available choices separated by newlines. A'
                           ' blank line ends the input\nEnter the zero-based'
                           ' index of your selection')

    @staticmethod
    def test_choices_saves_single_choice_when_called_with_single_choice(
            new_runner: NewRunner, choices_runner: InputRunner,
            test_data_dir: Path, starting_graph: Graph,
    ) -> None:
        new_runner()
        choices_runner('choice1\n\n0')

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_choices_draws_graph(
            new_runner: NewRunner, test_data_dir: Path, mock_draw: Mock,
            choices_runner: InputRunner,
    ) -> None:
        new_runner()
        choices_runner('choice1\n\n0')

        assert_draw_called(mock_draw, test_data_dir, expected_calls=2)

    @staticmethod
    def test_choices_exits_with_error_when_called_with_no_choices(
            new_runner: NewRunner, choices_runner: InputRunner,
    ) -> None:
        new_runner()
        assert_error_exit(choices_runner('\n'),
                          'At least one choice must be entered')

    @staticmethod
    @mark.parametrize('index', [1, 2, -2])
    def test_choices_exits_with_error_when_selected_choice_is_out_of_bounds(
            index: int, new_runner: NewRunner, choices_runner: InputRunner,
    ) -> None:
        new_runner()
        assert_error_exit(choices_runner(f'choice1\n\n{index}'),
                          f'Index {index} is out of bounds')

    @staticmethod
    def test_choices_exits_with_error_when_selected_choice_is_not_a_number(
            new_runner: NewRunner, choices_runner: InputRunner,
    ) -> None:
        new_runner()
        assert_error_exit(choices_runner('choice1\n\nnot_a_number'),
                          'Index not_a_number is not a number')

    @staticmethod
    def test_choices_aborts_if_project_does_not_exist(
            choices_runner: InputRunner,
    ) -> None:
        assert_error_exit(choices_runner('choice\n\n'),
                          'Project test_name does not exist')


class TestEndingCommand:
    @staticmethod
    @fixture
    def ending_runner(cli_runner: CliRunner) -> InputRunner:
        return lambda input_: cli_runner.invoke(app, ['test_name', 'ending'],
                                                input=input_)

    @staticmethod
    def test_ending_aborts_if_project_does_not_exist(
            ending_runner: InputRunner,
    ) -> None:
        assert_error_exit(ending_runner('ending\n'),
                          'Project test_name does not exist')

    @staticmethod
    def test_ending_aborts_when_called_before_any_choice_is_added(
            new_runner: NewRunner, ending_runner: InputRunner,
    ) -> None:
        new_runner()
        assert_error_exit(ending_runner('ending\n'),
                          "You cannot add an ending directly to the start"
                          " node")

    @staticmethod
    def test_ending_aborts_when_called_with_non_integer_id(
            new_runner: NewRunner, choices_runner: InputRunner,
            ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        new_runner()
        choices_runner('choice1\n\n0')
        assert_error_exit(ending_runner('ending\ninvalid_index\n'),
                          "The id must be an integer")

    @staticmethod
    def test_ending_aborts_when_called_with_non_existing_id(
            new_runner: NewRunner, choices_runner: InputRunner,
            ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        new_runner()
        choices_runner('choice1\n\n0')
        assert_error_exit(ending_runner('ending\n999\n'),
                          "id 999 does not exist")

    @staticmethod
    def test_ending_exits_with_correct_messages_when_called_with_ending(
            new_runner: NewRunner, choices_runner: InputRunner,
            ending_runner: InputRunner,
    ) -> None:
        new_runner()
        choices_runner('choice1\nchoice2\n\n0')
        assert_normal_exit(ending_runner('ending\n1\n'),
                           "Enter the ending's label\nEnter the id of an"
                           ' existing choice to be selected as the current'
                           ' choice\n')

    @staticmethod
    def test_ending_adds_ending_node_and_changes_selected_node(
            new_runner: NewRunner, choices_runner: InputRunner,
            ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        new_runner()
        choices_runner('choice1\nchoice2\n\n1')
        ending_runner('ending_label\n1\n')

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1)
        add_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2, 'green')
        add_ending_node(expected, 'E1', 'E1. ending_label')
        add_edge(expected, 2, 'E1', 'green')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_ending_draws_graph(
            new_runner: NewRunner, test_data_dir: Path, mock_draw: Mock,
            choices_runner: InputRunner, ending_runner: InputRunner,
    ) -> None:
        new_runner()
        choices_runner('choice1\n\n0')
        ending_runner('ending_label\n1\n')

        assert_draw_called(mock_draw, test_data_dir, expected_calls=3)


class TestViewCommand:
    @staticmethod
    @fixture
    def view_runner(cli_runner: CliRunner) -> ViewRunner:
        def runner(project_name: str = 'test_name', input_: str = '') \
                -> Result:
            return cli_runner.invoke(app, [project_name, 'view'], input=input_)
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
    @mark.skip_mock_draw_autouse
    def test_view_shows_existing_graph(
            new_runner: NewRunner, view_runner: ViewRunner,
            test_data_dir: Path, mock_spawn: Mock,
    ) -> None:
        new_runner()
        view_runner(input_='test_viewer\n')

        assert get_image_dir(test_data_dir).exists()
        mock_spawn.assert_called_once_with(
            ['test_viewer', get_image_dir(test_data_dir)],
        )

    @staticmethod
    def test_view_exits_with_error_if_project_does_not_exist(
            view_runner: ViewRunner,
    ) -> None:
        assert_error_exit(view_runner(), 'Project test_name does not exist')
