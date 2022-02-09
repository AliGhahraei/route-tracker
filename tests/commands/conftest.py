import os
from pathlib import Path
from typing import Any, Generator, Optional
from unittest.mock import Mock, patch

from click.testing import Result
from pytest import FixtureRequest, fixture
from typer.testing import CliRunner

from tests.commands.helpers import Runner


@fixture
def runner(mock_copy_save_file: Mock) -> Runner:
    def cli_runner(*args: Any, **kwargs: Any) -> Result:
        return CliRunner(mix_stderr=False).invoke(
            *args,
            obj={'copy_save_file': mock_copy_save_file},
            **kwargs,
        )
    return cli_runner


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
        with patch('route_tracker.io.draw') as mock:
            yield mock


@fixture
def mock_copy_save_file() -> Mock:
    return Mock()
