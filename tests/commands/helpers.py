from pathlib import Path
from typing import Any, Callable, Protocol
from unittest.mock import ANY, Mock

from click.testing import Result

from route_tracker.graph import Graph

InputRunner = Callable[[str], Result]


def assert_stored_graph_equals(data_dir: Path, expected_graph: Graph) -> None:
    graph = Graph(get_project_dir(data_dir) / 'graph')
    assert graph.content == expected_graph.content


def assert_draw_called(mock_draw: Mock, data_dir: Path) -> None:
    mock_draw.assert_called_once_with(ANY, get_image_path(data_dir))


def assert_normal_exit(result: Result, message: str) -> None:
    assert message in result.stdout
    assert result.exit_code == 0


def assert_error_exit(result: Result, message: str) -> None:
    assert message in result.stderr
    assert result.exit_code == 1


def get_project_dir(data_dir: Path) -> Path:
    return data_dir / 'route-tracker' / 'test_name'


def get_image_path(data_dir: Path) -> Path:
    return get_project_dir(data_dir) / 'routes.png'


class Runner(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Result:
        pass
