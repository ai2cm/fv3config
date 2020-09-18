import unittest
from fv3config import (
    config_to_namelist,
    config_from_namelist,
    InvalidFileError,
    ConfigError,
    enable_restart,
)
import os
from copy import deepcopy
import yaml
import tempfile


TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(TEST_DIRECTORY, "c12_config.yml"), "r") as f:
    DEFAULT_CONFIG = yaml.safe_load(f)

one_item_namelist = """&fms_io_nml
    checksum_required = .false.
/
"""
one_item_dict = {"fms_io_nml": {"checksum_required": False}}

all_types_namelist = """&my_nml
    integer_option = 1
    float_option = 2.0
    string_option = 'three'
    true_option = .true.
    false_option = .false.
/
"""
all_types_dict = {
    "my_nml": {
        "integer_option": 1,
        "float_option": 2.0,
        "string_option": "three",
        "true_option": True,
        "false_option": False,
    }
}

restart_namelist_settings = {
    "fv_core_nml": {
        "external_ic": False,
        "nggps_ic": False,
        "make_nh": False,
        "mountain": True,
        "warm_start": True,
        "na_init": 0,
    }
}

empty_dict = {}

config_with_empty_namelist = {"namelist": {}}

config_with_empty_fv_core_and_coupler_nml = {
    "namelist": {"fv_core_nml": {}, "coupler_nml": {}}
}


class ConfigDictTests(unittest.TestCase):
    def setUp(self):
        self._run_directory_list = []

    def tearDown(self):
        for directory in self._run_directory_list:
            directory.cleanup()

    def make_run_directory(self, directory_name):
        directory = tempfile.TemporaryDirectory(directory_name)
        self._run_directory_list.append(directory)
        return directory.name

    def test_init_from_empty_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        open(namelist_filename, "a").close()
        config = config_from_namelist(namelist_filename)
        self.assertIsInstance(config, dict)

    def test_init_from_missing_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        with self.assertRaises(InvalidFileError):
            config_from_namelist(namelist_filename)

    def test_init_from_one_item_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        with open(namelist_filename, "w") as f:
            f.write(one_item_namelist)
        config = config_from_namelist(namelist_filename)
        self.assertEqual(config, one_item_dict)

    def test_init_from_many_item_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        with open(namelist_filename, "w") as f:
            f.write(all_types_namelist)
        config = config_from_namelist(namelist_filename)
        self.assertEqual(config, all_types_dict)

    def test_empty_write_to_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        config = {"namelist": {}}
        config_to_namelist(config, namelist_filename)
        self.assertTrue(os.path.isfile(namelist_filename))
        with open(namelist_filename, "r") as namelist_file:
            written_namelist = namelist_file.read()
        self.assertEqual(written_namelist, "")

    def test_one_item_write_to_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        config = {"namelist": deepcopy(one_item_dict)}
        config_to_namelist(config, namelist_filename)
        self.assertTrue(os.path.isfile(namelist_filename))
        with open(namelist_filename, "r") as namelist_file:
            written_namelist = namelist_file.read()
        self.assertEqual(written_namelist, one_item_namelist)

    def test_many_items_write_to_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        config = {"namelist": deepcopy(all_types_dict)}
        config_to_namelist(config, namelist_filename)
        self.assertTrue(os.path.isfile(namelist_filename))
        with open(namelist_filename, "r") as namelist_file:
            written_lines = namelist_file.readlines()
        target_lines = [line + "\n" for line in all_types_namelist.split("\n") if line]
        self.assertEqual(len(written_lines), len(target_lines))
        self.assertEqual(written_lines[0], target_lines[0])
        self.assertEqual(
            set(written_lines[1:6]), set(target_lines[1:6])
        )  # order doesn't matter
        self.assertEqual(written_lines[6:], target_lines[6:])

    def test_write_to_existing_namelist(self):
        rundir = self.make_run_directory("test_rundir")
        namelist_filename = os.path.join(rundir, "input.nml")
        with open(namelist_filename, "w") as f:
            f.write(one_item_namelist)
        config = {"namelist": deepcopy(all_types_dict)}
        config_to_namelist(config, namelist_filename)
        with open(namelist_filename, "r") as namelist_file:
            written_lines = namelist_file.readlines()
        target_lines = [line + "\n" for line in all_types_namelist.split("\n") if line]
        self.assertEqual(len(written_lines), len(target_lines))
        self.assertEqual(written_lines[0], target_lines[0])
        self.assertEqual(
            set(written_lines[1:6]), set(target_lines[1:6])
        )  # order doesn't matter
        self.assertEqual(written_lines[6:], target_lines[6:])

    def test_default_config_has_entries(self):
        config = DEFAULT_CONFIG.copy()
        self.assertTrue(len(config) > 0)
        self.assertIn("namelist", config)
        self.assertIsInstance(config["namelist"], dict)
        for name in ["diag_table", "data_table", "forcing"]:
            self.assertIn(name, config)
            self.assertIsInstance(config[name], str)
        for name, value in config.items():
            self.assertIsInstance(name, str, f"key {name} is not a string")


class EnableRestartTests(unittest.TestCase):
    def assert_dict_in_and_equal(self, source_dict, target_dict):
        for name, item in source_dict.items():
            self.assertIn(name, target_dict)
            if isinstance(item, dict):
                self.assert_dict_in_and_equal(item, target_dict[name])
            else:
                self.assertEqual(item, target_dict[name])

    def test_enable_restart_from_default(self):
        config = DEFAULT_CONFIG.copy()
        restart_config = enable_restart(config, "initial_conditions")
        self.assert_dict_in_and_equal(
            restart_namelist_settings, restart_config["namelist"]
        )

    def test_enable_restart_from_empty_namelist(self):
        config = enable_restart(config_with_empty_namelist, "initial_conditions")
        assert config["namelist"]["fv_core_nml"]["warm_start"]
        assert not config["namelist"]["coupler_nml"]["force_date_from_namelist"]

    def test_enable_restart_from_empty_config(self):
        with self.assertRaises(ConfigError):
            enable_restart(empty_dict, "initial_conditions")

    def test_enable_restart_makes_copy(self):
        config = DEFAULT_CONFIG.copy()
        restart_config = enable_restart(config, "initial_conditions")
        self.assertEqual(config, DEFAULT_CONFIG)
        restart_config["diag_table"] = "changed item"
        restart_config["namelist"]["fv_core_nml"]["npx"] = 0
        self.assertEqual(config, DEFAULT_CONFIG)

    def test_enable_restart_initial_conditions(self):
        config = DEFAULT_CONFIG.copy()
        restart_config = enable_restart(config, "new_path")
        self.assertEqual(restart_config["initial_conditions"], "new_path")


if __name__ == "__main__":
    unittest.main()
