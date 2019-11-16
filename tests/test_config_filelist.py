import unittest
import os
import appdirs
from fv3config import (
    get_default_config, ConfigError,
)
from fv3config._config_filelist import (
    is_dict_or_list, get_orographic_forcing_filelist, get_base_forcing_filelist,
    get_initial_conditions_filelist, get_data_table_filelist_item, get_diag_table_filelist_item,
    get_field_table_filelist_item, generate_config_filelist_item, config_filelist_from_path,
    config_filelist_from_local_dir, config_filelist_from_gs_bucket, save_filelist_item
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
    'target_type': 'copy'
}

DEFAULT_DIAG_TABLE_FILELIST_ITEM = {
    'source_location': os.path.join(DATA_DIRECTORY, 'diag_table'),
    'source_name': 'diag_table_default',
    'target_location': '',
    'target_name': 'diag_table',
    'target_type': 'copy'
}

DEFAULT_FIELD_TABLE_FILELIST_ITEM = {
    'source_location': os.path.join(DATA_DIRECTORY, 'field_table'),
    'source_name': 'field_table_GFDLMP',
    'target_location': '',
    'target_name': 'field_table',
    'target_type': 'copy'
}


class ConfigFilelistTests(unittest.TestCase):

    def test_is_dict_or_list(self):
        empty_dict = {}
        empty_list = []
        self.assertTrue(is_dict_or_list(empty_dict))
        self.assertTrue(is_dict_or_list(empty_list))
        self.assertFalse(is_dict_or_list('a string'))
        self.assertFalse(is_dict_or_list(1.0))
        self.assertFalse(is_dict_or_list(1))

    def test_get_data_table_filelist_item_default(self):
        config = get_default_config()
        data_table_filelist_item = get_data_table_filelist_item(config)
        self.assertEqual(data_table_filelist_item, DEFAULT_DATA_TABLE_FILELIST_ITEM)

    def test_get_diag_table_filelist_item_default(self):
        config = get_default_config()
        diag_table_filelist_item = get_diag_table_filelist_item(config)
        self.assertEqual(diag_table_filelist_item, DEFAULT_DIAG_TABLE_FILELIST_ITEM)

    def test_get_field_table_filelist_item_default(self):
        config = get_default_config()
        field_table_filelist_item = get_field_table_filelist_item(config)
        self.assertEqual(field_table_filelist_item, DEFAULT_FIELD_TABLE_FILELIST_ITEM)


if __name__ == '__main__':
    unittest.main()
