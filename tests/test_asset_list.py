import unittest
import os
import shutil
import fv3config
from fv3config._asset_list import (
    is_dict_or_list, get_data_table_asset, get_diag_table_asset,
    get_field_table_asset, generate_asset, ensure_is_list,
    asset_list_from_local_dir, check_asset_has_required_keys, write_asset
)


TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
DATA_DIRECTORY = os.path.join(os.path.dirname(TEST_DIRECTORY), 'fv3config', 'data')

DEFAULT_DATA_TABLE_ASSET = {
    'source_location': os.path.join(DATA_DIRECTORY, 'data_table'),
    'source_name': 'data_table_default',
    'target_location': '',
    'target_name': 'data_table',
    'copy_method': 'copy'
}

DEFAULT_DIAG_TABLE_ASSET = {
    'source_location': os.path.join(DATA_DIRECTORY, 'diag_table'),
    'source_name': 'diag_table_default',
    'target_location': '',
    'target_name': 'diag_table',
    'copy_method': 'copy'
}

DEFAULT_FIELD_TABLE_ASSET = {
    'source_location': os.path.join(DATA_DIRECTORY, 'field_table'),
    'source_name': 'field_table_GFDLMP',
    'target_location': '',
    'target_name': 'field_table',
    'copy_method': 'copy'
}

SAMPLE_SOURCE_LOCATION = 'source/dir'
SAMPLE_SOURCE_NAME = 'filename'
SAMPLE_TARGET_LOCATION = 'target/dir'
SAMPLE_TARGET_NAME = 'target_filename'
SAMPLE_COPY_METHOD = 'link'

SAMPLE_ASSET_NO_KWARGS = {
    'source_location': SAMPLE_SOURCE_LOCATION,
    'source_name': SAMPLE_SOURCE_NAME,
    'target_location': '',
    'target_name': SAMPLE_SOURCE_NAME,
    'copy_method': 'copy',
}

SAMPLE_ASSET_WITH_KWARGS = {
    'source_location': SAMPLE_SOURCE_LOCATION,
    'source_name': SAMPLE_SOURCE_NAME,
    'target_location': SAMPLE_TARGET_LOCATION,
    'target_name': SAMPLE_TARGET_NAME,
    'copy_method': SAMPLE_COPY_METHOD,
}

TEST_SOURCE_DIR = 'test_source_dir'

FILELIST_EMPTY = []

FILELIST_ONE_FILE_IN_ROOT = [
    'file_in_root_dir',
]

FILELIST_WITH_SUBDIR = [
    os.path.join('subdir', 'file_in_subdir'),
    'file_in_root_dir',
]

ASSET_FILE_IN_ROOT_DIR = {
    'source_location': TEST_SOURCE_DIR,
    'source_name': 'file_in_root_dir',
    'target_location': '',
    'target_name': 'file_in_root_dir',
    'copy_method': 'copy',
}

ASSET_FILE_IN_SUBDIR = {
    'source_location': os.path.join(TEST_SOURCE_DIR, 'subdir'),
    'source_name': 'file_in_subdir',
    'target_location': 'subdir',
    'target_name': 'file_in_subdir',
    'copy_method': 'copy',
}

ASSET_LIST_EMPTY = []
ASSET_LIST_ONE_FILE_IN_ROOT = [ASSET_FILE_IN_ROOT_DIR]
ASSET_LIST_WITH_SUBDIR = [ASSET_FILE_IN_ROOT_DIR, ASSET_FILE_IN_SUBDIR]


class WorkDirectory(object):

    def __init__(self, directory_path):
        os.mkdir(directory_path)
        self.directory_path = directory_path

    def cleanup(self):
        shutil.rmtree(self.directory_path)


class AssetListTests(unittest.TestCase):

    def setUp(self):
        self._work_directory_list = []

    def tearDown(self):
        for directory in self._work_directory_list:
            directory.cleanup()

    def make_work_directory(self, directory_name):
        full_path = os.path.join(TEST_DIRECTORY, directory_name)
        self._work_directory_list.append(WorkDirectory(full_path))
        return full_path

    def test_is_dict_or_list(self):
        empty_dict = {}
        empty_list = []
        self.assertTrue(is_dict_or_list(empty_dict))
        self.assertTrue(is_dict_or_list(empty_list))
        self.assertFalse(is_dict_or_list('a string'))
        self.assertFalse(is_dict_or_list(1.0))
        self.assertFalse(is_dict_or_list(1))

    def test_get_data_table_asset_default(self):
        config = fv3config.get_default_config()
        data_table_asset = get_data_table_asset(config)
        self.assertEqual(data_table_asset, DEFAULT_DATA_TABLE_ASSET)

    def test_get_diag_table_asset_default(self):
        config = fv3config.get_default_config()
        diag_table_asset = get_diag_table_asset(config)
        self.assertEqual(diag_table_asset, DEFAULT_DIAG_TABLE_ASSET)

    def test_get_field_table_asset_default(self):
        config = fv3config.get_default_config()
        field_table_asset = get_field_table_asset(config)
        self.assertEqual(field_table_asset, DEFAULT_FIELD_TABLE_ASSET)

    def test_ensure_is_list(self):
        sample_dict = {}
        sample_list = []
        sample_float = 1.0
        self.assertIsInstance(ensure_is_list(sample_dict), list)
        self.assertIsInstance(ensure_is_list(sample_list), list)
        with self.assertRaises(fv3config.ConfigError):
            ensure_is_list(sample_float)

    def test_generate_asset_default_options(self):
        test_asset = generate_asset(SAMPLE_SOURCE_LOCATION, SAMPLE_SOURCE_NAME)
        self.assertEqual(test_asset, SAMPLE_ASSET_NO_KWARGS)

    def test_generate_asset_custom_options(self):
        test_asset = generate_asset(SAMPLE_SOURCE_LOCATION, SAMPLE_SOURCE_NAME,
                                    target_location=SAMPLE_TARGET_LOCATION,
                                    target_name=SAMPLE_TARGET_NAME,
                                    copy_method=SAMPLE_COPY_METHOD)
        self.assertEqual(test_asset, SAMPLE_ASSET_WITH_KWARGS)

    def test_asset_list_from_local_dir_empty(self):
        workdir = self.make_work_directory('workdir_empty')
        self.make_empty_files(workdir, FILELIST_EMPTY)
        asset_list = asset_list_from_local_dir(workdir)
        self.assertEqual(asset_list, ASSET_LIST_EMPTY)

    def test_asset_list_from_local_dir_one_file_in_root(self):
        workdir = self.make_work_directory('workdir_with_files')
        self.make_empty_files(os.path.join(workdir, TEST_SOURCE_DIR),
                              FILELIST_ONE_FILE_IN_ROOT)
        asset_list = asset_list_from_local_dir(os.path.join(workdir, TEST_SOURCE_DIR))
        # necessary to have full path for source location in test assets
        for asset in ASSET_LIST_ONE_FILE_IN_ROOT:
            asset['source_location'] = os.path.join(workdir, asset['source_location'])
        self.assertEqual(asset_list, ASSET_LIST_ONE_FILE_IN_ROOT)

    def test_asset_list_from_local_dir_with_subdir(self):
        workdir = self.make_work_directory('workdir_with_files')
        self.make_empty_files(os.path.join(workdir, TEST_SOURCE_DIR), FILELIST_WITH_SUBDIR)
        asset_list = asset_list_from_local_dir(os.path.join(workdir, TEST_SOURCE_DIR))
        # necessary to have full path for source location in test assets
        for asset in ASSET_LIST_WITH_SUBDIR:
            asset['source_location'] = os.path.join(workdir, asset['source_location'])
        self.assertEqual(asset_list, ASSET_LIST_WITH_SUBDIR)

    @staticmethod
    def make_empty_files(directory, filelist):
        for path in filelist:
            full_path = os.path.join(directory, path)
            head, tail = os.path.split(full_path)
            if not os.path.exists(head):
                os.makedirs(head)
            open(full_path, 'a').close()

    def test_check_asset_has_required_keys_bad_asset(self):
        bad_asset_dict = {'irrelevant_key': ''}
        with self.assertRaises(fv3config.ConfigError):
            check_asset_has_required_keys(bad_asset_dict)

    def test_check_asset_has_required_keys_proper_asset(self):
        proper_asset_dict = {
            'source_location': '',
            'source_name': '',
            'target_location': '',
            'target_name': '',
            'copy_method': '',
        }
        try:
            check_asset_has_required_keys(proper_asset_dict)
        except fv3config.ConfigError:
            self.fail("check_asset_valid raised ConfigError unexpectedly")

    def test_write_asset(self):
        source_workdir = self.make_work_directory('source_workdir')
        target_workdir = self.make_work_directory('target_workdir')
        test_filename = 'test_file'
        test_asset = {
            'source_location': source_workdir,
            'source_name': test_filename,
            'target_location': '',
            'target_name': test_filename,
            'copy_method': 'copy',
        }
        self.make_empty_files(source_workdir, [test_filename])
        write_asset(test_asset, target_workdir)
        self.assertTrue(os.path.exists(os.path.join(target_workdir, test_filename)))


if __name__ == '__main__':
    unittest.main()