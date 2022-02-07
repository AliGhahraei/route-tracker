import os
from pathlib import Path
from typing import Generator, Optional
from unittest.mock import Mock, patch

from pytest import FixtureRequest, fixture
from typer.testing import CliRunner


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
        with patch('route_tracker.io.draw') as mock:
            yield mock
