from pathlib import Path
from unittest.mock import Mock

from pytest import fixture

from route_tracker.commands import app
from route_tracker.graph import (Graph, add_edge, add_ending_node, add_node,
                                 add_selected_node)
from route_tracker.io import (store_choices_and_selection, store_ending,
                              store_new_project)
from tests.commands.helpers import (InputRunner, Runner, assert_draw_called,
                                    assert_error_exit, assert_normal_exit,
                                    assert_stored_graph_equals)


class TestAddEndingCommand:
    @staticmethod
    @fixture
    def add_ending_runner(runner: Runner) -> InputRunner:
        return lambda input_: runner(
            app, ['test_name', 'ending', 'add'], input=input_,
        )

    @staticmethod
    def test_add_aborts_if_project_does_not_exist(
            add_ending_runner: InputRunner,
    ) -> None:
        assert_error_exit(add_ending_runner('ending\n0'),
                          'Project test_name does not exist')

    @staticmethod
    def test_add_aborts_when_called_with_non_existing_id(
            add_ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1'], 0)
        assert_error_exit(add_ending_runner('ending\n999\n'),
                          "id 999 does not exist")

    @staticmethod
    def test_add_exits_with_correct_messages_when_called_with_ending(
            add_ending_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        assert_normal_exit(add_ending_runner('ending\n1\n'),
                           'Ending label: ending\nNew choice id: 1\n')

    @staticmethod
    def test_add_adds_ending_node_and_changes_selected_node(
            add_ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 1)
        add_ending_runner('ending_label\n1\n')

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1)
        add_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2, 'green')
        add_ending_node(expected, 'E0', 'E0. ending_label')
        add_edge(expected, 2, 'E0', 'green')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_add_draws_graph(
            test_data_dir: Path, mock_draw: Mock,
            add_ending_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1'], 0)
        add_ending_runner('ending_label\n1\n')

        assert_draw_called(mock_draw, test_data_dir)


class TestLinkEndingCommand:
    @staticmethod
    @fixture
    def link_ending_runner(runner: Runner) -> InputRunner:
        return lambda input_: runner(
            app, ['test_name', 'ending', 'link'], input=input_,
        )

    @staticmethod
    def test_link_aborts_if_project_does_not_exist(
            link_ending_runner: InputRunner,
    ) -> None:
        assert_error_exit(link_ending_runner('E0\n0'),
                          'Project test_name does not exist')

    @staticmethod
    def test_link_aborts_when_called_with_non_existing_ending_id(
            link_ending_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(link_ending_runner('E0\n0'),
                          "id E0 does not exist")

    @staticmethod
    def test_link_aborts_when_called_with_non_existing_id(
            link_ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        store_ending(info, 'ending', 2)
        assert_error_exit(link_ending_runner('E0\n999'),
                          "id 999 does not exist")

    @staticmethod
    def test_link_exits_with_correct_messages_when_called_with_ending(
            link_ending_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        store_ending(info, 'ending', 2)
        assert_normal_exit(link_ending_runner('E0\n0'),
                           'Ending id: E0\nNew choice id: 0\n')

    @staticmethod
    def test_link_adds_ending_node_and_changes_selected_node(
            link_ending_runner: InputRunner, starting_graph: Graph,
            test_data_dir: Path,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        store_ending(info, 'ending', 2)
        link_ending_runner('E0\n1')

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        add_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2)
        add_ending_node(expected, 'E0', 'E0. ending')
        add_edge(expected, 1, 'E0', 'green')
        add_edge(expected, 2, 'E0', 'blue')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_link_draws_graph(
            test_data_dir: Path, mock_draw: Mock,
            link_ending_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        store_ending(info, 'ending', 2)
        link_ending_runner('E0\n1')

        assert_draw_called(mock_draw, test_data_dir)
