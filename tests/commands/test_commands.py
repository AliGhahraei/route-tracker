#!/usr/bin/env python3
from pathlib import Path
from typing import Protocol
from unittest.mock import Mock

from click.testing import Result
from pytest import fixture, mark
from typer.testing import CliRunner

from route_tracker.commands import app
from route_tracker.graph import Graph, add_selected_node
from route_tracker.io import store_new_project
from tests.commands.helpers import (assert_draw_called, assert_error_exit,
                                    assert_normal_exit,
                                    assert_stored_graph_equals, get_image_dir)


class NewRunner(Protocol):
    def __call__(self, project_name: str = ...) -> Result:
        pass


class ViewRunner(Protocol):
    def __call__(self, project_name: str = ..., input_: str = ...) -> Result:
        pass


class TestNewCommand:
    @staticmethod
    @fixture
    def new_runner(cli_runner: CliRunner) -> NewRunner:
        def runner(project_name: str = 'test_name') -> Result:
            return cli_runner.invoke(app, [project_name, 'new'])

        return runner

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
            view_runner: ViewRunner,
    ) -> None:
        store_new_project('test_name')
        assert_normal_exit(view_runner(input_='test_viewer\n'),
                           'Image viewer command:')

    @staticmethod
    def test_view_does_not_prompt_for_viewer_if_configured(
            view_runner: ViewRunner,
    ) -> None:
        store_new_project('test_name')
        view_runner(input_='test_viewer\n')
        assert_normal_exit(view_runner(), '')

    @staticmethod
    @mark.skip_mock_draw_autouse
    def test_view_shows_existing_graph(
            view_runner: ViewRunner, test_data_dir: Path, mock_spawn: Mock,
    ) -> None:
        store_new_project('test_name')
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
