import unittest
import os
import tempfile
import fv3config
from fv3config._asset_list import (
    is_dict_or_list, get_orographic_forcing_asset_list, get_base_forcing_asset_list,
    get_initial_conditions_asset_list, get_data_table_asset, get_diag_table_asset,
    get_field_table_asset, generate_asset, asset_list_from_path, ensure_is_list,
    asset_list_from_local_dir, asset_list_from_gs_bucket, write_asset, write_asset_list,
)
from fv3config._datastore import get_cache_dir


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

SAMPLE_ASSET_DEFAULT_OPTS = {
    'source_location': SAMPLE_SOURCE_LOCATION,
    'source_name': SAMPLE_SOURCE_NAME,
    'target_location': '',
    'target_name': SAMPLE_SOURCE_NAME,
    'copy_method': 'copy',
}

SAMPLE_ASSET_CUSTOM_OPTS = {
    'source_location': SAMPLE_SOURCE_LOCATION,
    'source_name': SAMPLE_SOURCE_NAME,
    'target_location': SAMPLE_TARGET_LOCATION,
    'target_name': SAMPLE_TARGET_NAME,
    'copy_method': SAMPLE_COPY_METHOD,
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
        self.assertEqual(test_asset, SAMPLE_ASSET_DEFAULT_OPTS)

    def test_generate_asset_custom_options(self):
        test_asset = generate_asset(SAMPLE_SOURCE_LOCATION, SAMPLE_SOURCE_NAME,
                                    target_location=SAMPLE_TARGET_LOCATION,
                                    target_name=SAMPLE_TARGET_NAME,
                                    copy_method=SAMPLE_COPY_METHOD)
        self.assertEqual(test_asset, SAMPLE_ASSET_CUSTOM_OPTS)

if __name__ == '__main__':
    unittest.main()
