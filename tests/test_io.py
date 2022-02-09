from pathlib import Path
from shutil import copy2
from typing import Dict, Generator
from unittest.mock import Mock, patch

from pytest import fixture
from tomlkit import document, parse

from route_tracker.io import (copy_save_file, read_project_info,
                              store_new_project)
from route_tracker.projects import SaveFileInfo


@fixture
def common_fields() -> Dict[str, int]:
    return dict(
        last_generated_id=0,
        next_numeric_ending_id=0,
        last_choice_id=0,
        route_id=0,
    )


class TestCopySaveFile:
    @staticmethod
    @fixture
    def mock_copy() -> Generator[Mock, None, None]:
        with patch('route_tracker.io.copy2', spec_set=copy2) as mock:
            yield mock

    @staticmethod
    @fixture
    def file(tmp_path: Path) -> Path:
        return tmp_path / 'file'

    @staticmethod
    @fixture
    def target_dir(tmp_path: Path) -> Path:
        return tmp_path / 'deep' / 'target_dir'

    @staticmethod
    def test_copy_skips_copy_if_save_file_path_is_none(mock_copy: Mock) \
            -> None:
        copy_save_file(True, SaveFileInfo(route_id=1), 1)
        mock_copy.assert_not_called()

    @staticmethod
    def test_copy_skips_copy_if_save_is_false(file: Path, mock_copy: Mock,
                                              target_dir: Path) -> None:
        copy_save_file(False, SaveFileInfo(route_id=2, file=file,
                                           target_directory=target_dir), 1)
        mock_copy.assert_not_called()

    @staticmethod
    def test_copy_copies_if_save_file_path_is_set(file: Path,
                                                  target_dir: Path) -> None:
        file.touch()
        copy_save_file(True, SaveFileInfo(route_id=2, file=file,
                                          target_directory=target_dir), 1)
        assert (target_dir / '1_2').exists()

    @staticmethod
    def test_copy_can_copy_twice_if_save_file_path_is_set(
            file: Path, target_dir: Path,
    ) -> None:
        file.touch()
        copy_save_file(True, SaveFileInfo(route_id=2, file=file,
                                          target_directory=target_dir), 1)

        copy_save_file(True, SaveFileInfo(route_id=4, file=file,
                                          target_directory=target_dir), 3)
        assert (target_dir / '1_2').exists()
        assert (target_dir / '3_4').exists()


class TestStoreNewProject:
    @staticmethod
    @fixture
    def data_path(test_data_dir: Path) -> Path:
        return test_data_dir / 'route-tracker' / 'test_name' / 'data'

    @staticmethod
    def test_store_stores_correct_document_with_all_fields(
            data_path: Path, common_fields: Dict[str, int],
    ) -> None:
        expected_doc = document()
        expected_doc.update(
            **common_fields,
            file='test/path',
            target_directory='test/dir',
        )

        store_new_project('test_name', Path('test/path'), Path('test/dir'))

        with open(data_path) as f:
            assert expected_doc == parse(f.read())

    @staticmethod
    def test_store_stores_correct_document_skipping_none_fields(
            data_path: Path, common_fields: Dict[str, int],
    ) -> None:
        expected_doc = document()
        expected_doc.update(common_fields)

        store_new_project('test_name')

        with open(data_path) as f:
            assert expected_doc == parse(f.read())


class TestReadProjectInfo:
    @staticmethod
    def test_read_gets_information_correctly_with_all_fields(
            common_fields: Dict[str, int],
    ) -> None:
        info = store_new_project('test_name', Path('test/path'),
                                 Path('test/dir'))
        assert read_project_info('test_name') == info

    @staticmethod
    def test_read_gets_information_correctly_skipping_none_fields(
            common_fields: Dict[str, int],
    ) -> None:
        info = store_new_project('test_name')
        assert read_project_info('test_name') == info
