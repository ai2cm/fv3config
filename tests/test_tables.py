import unittest
import copy
import os
import shutil
from fv3config import ConfigError
from fv3config._tables import update_diag_table_for_config
from fv3config.config.derive import (
    get_current_date,
    _get_current_date_from_coupler_res,
    _get_coupler_res_filename,
)
from fv3config._datastore import (
    get_microphysics_name,
    get_field_table_filename,
    get_diag_table_filename,
    get_data_table_filename,
)
import yaml
import tempfile

TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(TEST_DIRECTORY, "c12_config.yml"), "r") as f:
    DEFAULT_CONFIG = yaml.safe_load(f)


valid_coupler_res = """    2        (Calendar: no_calendar=0, thirty_day_months=1, julian=2, gregorian=3, noleap=4)
  2016     8     1     0     0     0        Model start time:   year, month, day, hour, minute, second
  2016     8     3     0     0     0        Current model time: year, month, day, hour, minute, second
/
"""

valid_current_date = [2016, 8, 3, 0, 0, 0]

bad_coupler_res = """    2        (Calendar: no_calendar=0, thirty_day_months=1, julian=2, gregorian=3, noleap=4)
  2016     8     1     0     0     0        Model start time:   year, month, day, hour, minute, second
  2016     8  missing  0     0     0        Current model time: year, month, day, hour, minute, second
/
"""

empty_config = {}

config_for_update_diag_table_test = {
    "experiment_name": "diag_table_test",
    "namelist": {
        "coupler_nml": {
            "current_date": valid_current_date,
            "force_date_from_namelist": True,
        }
    },
}

diag_table_test_in = "default_experiment\n2016 1 1 0 0 0\nother contents here"
diag_table_test_out = "diag_table_test\n2016 8 3 0 0 0\nother contents here"


class RunDirectory(object):
    def __init__(self, directory_path):
        os.mkdir(directory_path)
        os.mkdir(os.path.join(directory_path, "INPUT"))
        os.mkdir(os.path.join(directory_path, "RESTART"))
        self.directory_path = directory_path

    def cleanup(self):
        shutil.rmtree(self.directory_path)


class TableTests(unittest.TestCase):
    def setUp(self):
        self._run_directory_list = []

    def tearDown(self):
        for directory in self._run_directory_list:
            directory.cleanup()

    def make_run_directory(self, directory_name):
        full_path = os.path.join(TEST_DIRECTORY, directory_name)
        self._run_directory_list.append(RunDirectory(full_path))
        return full_path

    def test_default_data_table_filename(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        filename = get_data_table_filename(config)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue("data_table" in filename)

    def test_default_diag_table_filename(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        filename = get_diag_table_filename(config)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue("diag_table" in filename)

    def test_default_field_table_filename(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        filename = get_field_table_filename(config)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue("field_table" in filename)

    def test_get_specified_data_table_filename(self):
        source_rundir = self.make_run_directory("source_rundir")
        data_table_filename = os.path.join(source_rundir, "data_table")
        open(data_table_filename, "w").close()
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["data_table"] = data_table_filename
        filename = get_data_table_filename(config)
        self.assertEqual(filename, data_table_filename)

    def test_get_specified_diag_table_filename(self):
        source_rundir = self.make_run_directory("source_rundir")
        diag_table_filename = os.path.join(source_rundir, "diag_table")
        open(diag_table_filename, "w").close()
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["diag_table"] = diag_table_filename
        filename = get_diag_table_filename(config)
        self.assertEqual(filename, diag_table_filename)

    def test_get_bad_field_table_filename(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["namelist"]["gfs_physics_nml"]["imp_physics"] = -1
        with self.assertRaises(NotImplementedError):
            get_field_table_filename(config)

    def test_get_bad_microphysics_name_from_config(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["namelist"]["gfs_physics_nml"]["imp_physics"] = -1
        with self.assertRaises(NotImplementedError):
            get_microphysics_name(config)

    def test_get_bad_diag_table_filename(self):
        diag_table_filename = "/not/a/path/diag_table"
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["diag_table"] = diag_table_filename
        with self.assertRaises(ConfigError):
            get_diag_table_filename(config)

    def test_get_diag_table_from_empty_config(self):
        with self.assertRaises(ConfigError):
            get_diag_table_filename(empty_config)

    def test_get_data_table_from_empty_config(self):
        with self.assertRaises(ConfigError):
            get_data_table_filename(empty_config)

    def test_update_diag_table_from_empty_config(self):
        rundir = self.make_run_directory("rundir")
        with self.assertRaises(ConfigError):
            update_diag_table_for_config(
                empty_config, valid_current_date, os.path.join(rundir, "source")
            )

    def test_get_current_date_from_coupler_res(self):
        rundir = self.make_run_directory("test_rundir")
        coupler_res_filename = os.path.join(rundir, "coupler.res")
        with open(coupler_res_filename, "w") as f:
            f.write(valid_coupler_res)
        current_date = _get_current_date_from_coupler_res(coupler_res_filename)
        self.assertEqual(current_date, valid_current_date)

    def test_get_current_date_from_bad_coupler_res(self):
        rundir = self.make_run_directory("test_rundir")
        coupler_res_filename = os.path.join(rundir, "coupler.res")
        with open(coupler_res_filename, "w") as f:
            f.write(bad_coupler_res)
        with self.assertRaises(ConfigError):
            _get_current_date_from_coupler_res(coupler_res_filename)

    def test_get_current_date_from_config_force_date_true(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["namelist"]["coupler_nml"]["force_date_from_namelist"] = True
        config["namelist"]["coupler_nml"]["current_date"] = valid_current_date
        current_date = get_current_date(config)
        self.assertEqual(current_date, valid_current_date)

    def test_get_current_date_from_config_force_date_false(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["namelist"]["coupler_nml"]["force_date_from_namelist"] = False
        config["namelist"]["coupler_nml"]["current_date"] = valid_current_date
        current_date = get_current_date(config)
        self.assertEqual(current_date, valid_current_date)

    def test_get_current_date_from_config_which_includes_coupler_res_asset(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        tmpdir = self.make_run_directory("test_dir")
        config["patch_files"] = {
            "source_location": tmpdir,
            "source_name": "coupler.res",
            "target_location": "INPUT",
            "target_name": "coupler.res",
            "copy_method": "copy",
        }
        with open(os.path.join(tmpdir, "coupler.res"), "w") as f:
            f.write(valid_coupler_res)
        current_date = get_current_date(config)
        self.assertEqual(current_date, valid_current_date)

    def test_get_coupler_res_filename_from_bytes_coupler_res_asset(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["patch_files"] = {
            "bytes": b"some data",
            "target_location": "INPUT",
            "target_name": "coupler.res",
        }
        with self.assertRaises(NotImplementedError):
            _get_coupler_res_filename(config)

    def test_get_current_date_from_config_empty_initial_conditions(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["initial_conditions"] = []
        config["namelist"]["coupler_nml"]["current_date"] = valid_current_date
        current_date = get_current_date(config)
        self.assertEqual(current_date, valid_current_date)

    def test_update_diag_table_for_config(self):
        rundir = self.make_run_directory("test_rundir")
        diag_table_filename = os.path.join(rundir, "diag_table")
        with open(diag_table_filename, "w") as f:
            f.write(diag_table_test_in)
        current_date = get_current_date(config_for_update_diag_table_test)
        update_diag_table_for_config(
            config_for_update_diag_table_test, current_date, diag_table_filename
        )
        with open(diag_table_filename) as f:
            self.assertEqual(diag_table_test_out, f.read())


def test_get_coupler_res_filename_from_dir():
    config = copy.deepcopy(DEFAULT_CONFIG)
    with tempfile.TemporaryDirectory() as initial_conditions_dir:
        coupler_res_filename = os.path.join(initial_conditions_dir, "coupler.res")
        with open(coupler_res_filename, "w") as f:
            f.write(valid_coupler_res)
        config["initial_conditions"] = initial_conditions_dir
        result = _get_coupler_res_filename(config)
        assert result == coupler_res_filename


if __name__ == "__main__":
    unittest.main()
