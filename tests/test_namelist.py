import unittest
from fv3config import config_to_namelist, config_from_namelist, InvalidFileError, get_default_config, enable_restart
import os
import shutil
import f90nml
from copy import deepcopy


test_directory = os.path.dirname(os.path.realpath(__file__))


one_item_namelist = """&fms_io_nml
    checksum_required = .false.
/
"""
one_item_dict = {
    'fms_io_nml': {
        'checksum_required': False
    }
}

all_types_namelist = """&my_nml
    integer_option = 1
    float_option = 2.0
    string_option = 'three'
    true_option = .true.
    false_option = .false.
/
"""
all_types_dict = {
    'my_nml': {
        'integer_option': 1,
        'float_option': 2.,
        'string_option': 'three',
        'true_option': True,
        'false_option': False,
    }
}

restart_namelist_settings = {
    'fv_core_nml': {
        'external_ic': False,
        'nggps_ic': False,
        'make_nh': False,
        'mountain': True,
        'warm_start': True,
         'na_init': 0,
    }
}


class RunDirectory(object):

    def __init__(self, directory_path):
        os.mkdir(directory_path)
        self.directory_path = directory_path

    def cleanup(self):
        shutil.rmtree(self.directory_path)


class ConfigDictTests(unittest.TestCase):

    def setUp(self):
        self._run_directory_list = []

    def tearDown(self):
        for directory in self._run_directory_list:
            directory.cleanup()

    def make_run_directory(self, directory_name):
        full_path = os.path.join(test_directory, directory_name)
        self._run_directory_list.append(RunDirectory(full_path))
        return full_path

    def test_init_from_empty_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        open(namelist_filename, 'a').close()
        config = config_from_namelist(namelist_filename)
        self.assertIsInstance(config, dict)

    def test_init_from_missing_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        with self.assertRaises(InvalidFileError):
            config_from_namelist(namelist_filename)

    def test_init_from_one_item_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        with open(namelist_filename, 'w') as f:
            f.write(one_item_namelist)
        config = config_from_namelist(namelist_filename)
        self.assertEqual(config, one_item_dict)

    def test_init_from_many_item_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        with open(namelist_filename, 'w') as f:
            f.write(all_types_namelist)
        config = config_from_namelist(namelist_filename)
        self.assertEqual(config, all_types_dict)

    def test_empty_write_to_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        config = {'namelist': {}}
        config_to_namelist(config, namelist_filename)
        self.assertTrue(os.path.isfile(namelist_filename))
        with open(namelist_filename, 'r') as namelist_file:
            written_namelist = namelist_file.read()
        self.assertEqual(written_namelist, '')

    def test_one_item_write_to_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        config = {'namelist': deepcopy(one_item_dict)}
        config_to_namelist(config, namelist_filename)
        self.assertTrue(os.path.isfile(namelist_filename))
        with open(namelist_filename, 'r') as namelist_file:
            written_namelist = namelist_file.read()
        self.assertEqual(written_namelist, one_item_namelist)

    def test_many_items_write_to_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        config = {'namelist': deepcopy(all_types_dict)}
        config_to_namelist(config, namelist_filename)
        self.assertTrue(os.path.isfile(namelist_filename))
        with open(namelist_filename, 'r') as namelist_file:
            written_lines = namelist_file.readlines()
        target_lines = [line + '\n' for line in all_types_namelist.split('\n') if line]
        self.assertEqual(len(written_lines), len(target_lines))
        self.assertEqual(written_lines[0], target_lines[0])
        self.assertEqual(set(written_lines[1:6]), set(target_lines[1:6]))  # order doesn't matter
        self.assertEqual(written_lines[6:], target_lines[6:])

    def test_write_to_existing_namelist(self):
        rundir = self.make_run_directory('test_rundir')
        namelist_filename = os.path.join(rundir, 'input.nml')
        with open(namelist_filename, 'w') as f:
            f.write(one_item_namelist)
        config = {'namelist': deepcopy(all_types_dict)}
        config_to_namelist(config, namelist_filename)
        with open(namelist_filename, 'r') as namelist_file:
            written_lines = namelist_file.readlines()
        target_lines = [line + '\n' for line in all_types_namelist.split('\n') if line]
        self.assertEqual(len(written_lines), len(target_lines))
        self.assertEqual(written_lines[0], target_lines[0])
        self.assertEqual(set(written_lines[1:6]), set(target_lines[1:6]))  # order doesn't matter
        self.assertEqual(written_lines[6:], target_lines[6:])

    def test_default_config_has_entries(self):
        config = get_default_config()
        self.assertTrue(len(config) > 0)
        self.assertIn('namelist', config)
        self.assertIsInstance(config['namelist'], dict)
        for name in ['diag_table', 'data_table', 'forcing']:
            self.assertIn(name, config)
            self.assertIsInstance(config[name], str)
        for name, value in config.items():
            self.assertIsInstance(name, str, f'key {name} is not a string')

    def test_enable_restart_from_default(self):
        config = get_default_config()
        enable_restart(config)
        for nml in restart_namelist_settings:
            for param in restart_namelist_settings[nml]:
                self.assertEqual(config['namelist'][nml][param],
                                 restart_namelist_settings[nml][param])


if __name__ == '__main__':
    unittest.main()
