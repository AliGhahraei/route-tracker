from pathlib import Path
from unittest.mock import Mock

from pytest import fixture, mark

from route_tracker.commands import app
from route_tracker.graph import (Graph, add_edge, add_node, add_selected_node,
                                 comment_node, select_node)
from route_tracker.io import store_choices_and_selection, store_new_project
from tests.commands.helpers import (InputRunner, Runner, assert_draw_called,
                                    assert_error_exit, assert_normal_exit,
                                    assert_stored_graph_equals)


class TestAddChoicesCommand:
    @staticmethod
    @fixture
    def add_choices_runner(runner: Runner, mock_copy_save_file: Mock) \
            -> InputRunner:
        return lambda input_: runner(
            app, ['test_name', 'choices', 'add'], input=input_,
        )

    @staticmethod
    def test_add_exits_with_correct_messages_when_called_with_choices(
            add_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_normal_exit(add_choices_runner('choice1\n\n0'),
                           'Enter available choices separated by newlines. A'
                           ' blank line ends the input\nEnter the zero-based'
                           ' index of your selection')

    @staticmethod
    def test_add_saves_single_choice_when_called_with_single_choice(
            add_choices_runner: InputRunner, test_data_dir: Path,
            starting_graph: Graph,
    ) -> None:
        store_new_project('test_name')
        add_choices_runner('choice1\n\n0')

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_add_draws_graph(
            test_data_dir: Path, mock_draw: Mock,
            add_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        add_choices_runner('choice1\n\n0')

        assert_draw_called(mock_draw, test_data_dir)

    @staticmethod
    def test_add_exits_with_error_when_called_with_no_choices(
            add_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(add_choices_runner('\n'),
                          'At least one choice must be entered')

    @staticmethod
    @mark.parametrize('index', [1, 2, -2])
    def test_add_exits_with_error_when_selected_choice_is_out_of_bounds(
            index: int, add_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(add_choices_runner(f'choice1\n\n{index}'),
                          f'Index {index} is out of bounds')

    @staticmethod
    def test_add_exits_with_error_when_selected_choice_is_not_a_number(
            add_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(add_choices_runner('choice1\n\nnot_a_number'),
                          'Index not_a_number is not a number')

    @staticmethod
    def test_add_aborts_if_project_does_not_exist(
            add_choices_runner: InputRunner,
    ) -> None:
        assert_error_exit(add_choices_runner('choice\n\n'),
                          'Project test_name does not exist')


class TestAdvanceChoice:
    @staticmethod
    @fixture
    def advance_choices_runner(runner: Runner,
                               mock_copy_save_file: Mock) -> InputRunner:
        return lambda input_: runner(
            app, ['test_name', 'choices', 'advance'], input=input_,
        )

    @staticmethod
    def test_advance_aborts_if_project_does_not_exist(
            advance_choices_runner: InputRunner,
    ) -> None:
        assert_error_exit(advance_choices_runner('0'),
                          'Project test_name does not exist')

    @staticmethod
    def test_advance_aborts_when_called_with_non_existing_id(
            advance_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(advance_choices_runner('999'),
                          "id 999 does not exist")

    @staticmethod
    def test_advance_aborts_when_called_with_currently_selected_id(
            advance_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(advance_choices_runner('0'),
                          "Cannot advance currently selected node to itself")

    @staticmethod
    def test_advance_advances_to_id(
            test_data_dir: Path, starting_graph: Graph,
            advance_choices_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        advance_choices_runner('2')

        expected = starting_graph
        add_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        add_selected_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2)
        add_edge(expected, 1, 2, 'green')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_advance_draws_image(
            test_data_dir: Path, mock_draw: Mock,
            advance_choices_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        advance_choices_runner('2')

        assert_draw_called(mock_draw, test_data_dir)


class TestLinkChoices:
    @staticmethod
    @fixture
    def link_choices_runner(runner: Runner) -> InputRunner:
        return lambda input_: runner(
            app, ['test_name', 'choices', 'link'], input=input_,
        )

    @staticmethod
    def test_link_aborts_if_project_does_not_exist(
            link_choices_runner: InputRunner,
    ) -> None:
        assert_error_exit(link_choices_runner('0'),
                          'Project test_name does not exist')

    @staticmethod
    def test_link_aborts_when_called_with_non_existing_id(
            link_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(link_choices_runner('999'),
                          "id 999 does not exist")

    @staticmethod
    def test_link_aborts_when_called_with_currently_selected_id(
            link_choices_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(link_choices_runner('0'),
                          "Cannot link currently selected node to itself")

    @staticmethod
    def test_link_links_to_id(
            test_data_dir: Path, starting_graph: Graph,
            link_choices_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        link_choices_runner('2')

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        add_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2)
        add_edge(expected, 1, 2)
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_link_draws_image(
            test_data_dir: Path, mock_draw: Mock,
            link_choices_runner: InputRunner,
    ) -> None:
        info = store_new_project('test_name')
        store_choices_and_selection(info, ['choice1', 'choice2'], 0)
        link_choices_runner('2')

        assert_draw_called(mock_draw, test_data_dir)


class TestCommentChoice:
    @staticmethod
    @fixture
    def comment_choice_runner(runner: Runner) -> InputRunner:
        return lambda input_: runner(
            app, ['test_name', 'choices', 'comment'], input=input_,
        )

    @staticmethod
    def test_comment_aborts_if_project_does_not_exist(
            comment_choice_runner: InputRunner,
    ) -> None:
        assert_error_exit(comment_choice_runner('0\ncomment'),
                          'Project test_name does not exist')

    @staticmethod
    def test_comment_aborts_when_called_with_non_existing_id(
            comment_choice_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        assert_error_exit(comment_choice_runner('999\ncomment'),
                          "id 999 does not exist")

    @staticmethod
    def test_comment_adds_comment(
            test_data_dir: Path, starting_graph: Graph,
            comment_choice_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        comment_choice_runner('0\ncomment')

        expected = starting_graph
        select_node(expected, 0)
        comment_node(expected, 0, '0: comment')
        assert_stored_graph_equals(test_data_dir, expected)

    @staticmethod
    def test_comment_draws_image(
            test_data_dir: Path, mock_draw: Mock,
            comment_choice_runner: InputRunner,
    ) -> None:
        store_new_project('test_name')
        comment_choice_runner('0\ncomment')

        assert_draw_called(mock_draw, test_data_dir)
