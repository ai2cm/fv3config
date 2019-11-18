import unittest
import os
import appdirs
from fv3config import (
    get_default_config, ConfigError,
)
from fv3config._asset_list import (
    is_dict_or_list, get_orographic_forcing_asset_list, get_base_forcing_asset_list,
    get_initial_conditions_asset_list, get_data_table_asset, get_diag_table_asset,
    get_field_table_asset, generate_config_asset, asset_list_from_path,
    asset_list_from_local_dir, asset_list_from_gs_bucket, write_asset, write_asset_list
)


TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
DATA_DIRECTORY = os.path.join(os.path.dirname(TEST_DIRECTORY), 'fv3config', 'data')
LOCAL_ARCHIVE_DIR = os.path.join(appdirs.user_data_dir('fv3gfs', 'vulcan'),
                                 'archive')

DEFAULT_DATA_TABLE_FILELIST_ITEM = {
    'source_location': os.path.join(DATA_DIRECTORY, 'data_table'),
    'source_name': 'data_table_default',
    'target_location': '',
    'target_name': 'data_table',
    'copy_method': 'copy'
}

DEFAULT_DIAG_TABLE_FILELIST_ITEM = {
    'source_location': os.path.join(DATA_DIRECTORY, 'diag_table'),
    'source_name': 'diag_table_default',
    'target_location': '',
    'target_name': 'diag_table',
    'copy_method': 'copy'
}

DEFAULT_FIELD_TABLE_FILELIST_ITEM = {
    'source_location': os.path.join(DATA_DIRECTORY, 'field_table'),
    'source_name': 'field_table_GFDLMP',
    'target_location': '',
    'target_name': 'field_table',
    'copy_method': 'copy'
}


class AssetListTests(unittest.TestCase):

    def test_is_dict_or_list(self):
        empty_dict = {}
        empty_list = []
        self.assertTrue(is_dict_or_list(empty_dict))
        self.assertTrue(is_dict_or_list(empty_list))
        self.assertFalse(is_dict_or_list('a string'))
        self.assertFalse(is_dict_or_list(1.0))
        self.assertFalse(is_dict_or_list(1))

    def test_get_data_table_asset_default(self):
        config = get_default_config()
        data_table_asset = get_data_table_asset(config)
        self.assertEqual(data_table_asset, DEFAULT_DATA_TABLE_FILELIST_ITEM)

    def test_get_diag_table_asset_default(self):
        config = get_default_config()
        diag_table_asset = get_diag_table_asset(config)
        self.assertEqual(diag_table_asset, DEFAULT_DIAG_TABLE_FILELIST_ITEM)

    def test_get_field_table_asset_default(self):
        config = get_default_config()
        field_table_asset = get_field_table_asset(config)
        self.assertEqual(field_table_asset, DEFAULT_FIELD_TABLE_FILELIST_ITEM)


if __name__ == '__main__':
    unittest.main()
