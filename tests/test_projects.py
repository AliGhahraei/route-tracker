#!/usr/bin/env python3
from pytest import mark

from route_tracker.graph import (Graph, add_edge, add_ending_node, add_node,
                                 add_selected_node)
from route_tracker.projects import (ProjectInfo, add_choices_and_selection,
                                    add_ending, create_project,
                                    get_route_color)


def assert_graphs_equal(info: ProjectInfo, expected_graph: Graph) -> None:
    assert info.graph.content == expected_graph.content


class TestGetRouteColor:
    @staticmethod
    @mark.parametrize('ending_id,expected_color', [
        (0, 'green'),
        (1, 'blue'),
        (11, 'darkgoldenrod'),
        (12, 'green'),
    ])
    def test_valid_id_returns_matching_color(ending_id: int,
                                             expected_color: str) -> None:
        assert get_route_color


class TestAddChoicesAndSelection:
    @staticmethod
    def test_add_saves_single_choice_when_called_with_single_choice(
            starting_graph: Graph,
    ) -> None:
        info = create_project('test_name')
        add_choices_and_selection(info, ['choice1'], 0)

        expected = starting_graph
        add_selected_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        assert_graphs_equal(info, expected)

    @staticmethod
    def test_add_saves_choices_when_called_with_multiple_choices(
            starting_graph: Graph,
    ) -> None:
        info = create_project('test_name')
        add_choices_and_selection(info, ['choice1', 'choice2'], 1)

        expected = starting_graph
        add_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1)
        add_selected_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2, 'green')
        assert_graphs_equal(info, expected)

    @staticmethod
    def test_add_saves_choices_when_called_with_multiple_add_commands(
            starting_graph: Graph,
    ) -> None:
        info = create_project('test_name')
        add_choices_and_selection(info, ['choice1', 'choice2'], 0)
        add_choices_and_selection(info, ['choice3', 'choice4'], 0)

        expected = starting_graph
        add_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1, 'green')
        add_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2)
        add_selected_node(expected, 3, '3. choice3')
        add_edge(expected, 1, 3, 'green')
        add_node(expected, 4, '4. choice4')
        add_edge(expected, 1, 4)
        assert_graphs_equal(info, expected)


class TestAddEnding:
    @staticmethod
    def test_add_adds_ending_nodes_with_different_edge_colors_and_ids(
            starting_graph: Graph,
    ) -> None:
        info = create_project('test_name')
        add_choices_and_selection(info, ['choice1', 'choice2'], 1)
        add_ending(info, 'ending1', 1)
        add_choices_and_selection(info, ['choice3'], 0)
        add_ending(info, 'ending2', 2)

        expected = starting_graph
        add_node(expected, 1, '1. choice1')
        add_edge(expected, 0, 1)
        add_selected_node(expected, 2, '2. choice2')
        add_edge(expected, 0, 2, 'green')
        add_ending_node(expected, 'E0', 'E0. ending1')
        add_edge(expected, 2, 'E0', 'green')
        add_node(expected, 3, '3. choice3')
        add_edge(expected, 1, 3, 'blue')
        add_ending_node(expected, 'E1', 'E1. ending2')
        add_edge(expected, 3, 'E1', 'blue')
        assert_graphs_equal(info, expected)
