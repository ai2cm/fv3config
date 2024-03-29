import unittest
import os
import tempfile
import fv3config
import fv3config.caching
from fv3config._datastore import (
    get_base_forcing_directory,
    get_orographic_forcing_directory,
    resolve_option,
)
from fv3config.config.initial_conditions import get_initial_conditions_directory
from fv3config._asset_list_config import (
    get_orographic_forcing_asset_list,
    get_base_forcing_asset_list,
)
from fv3config.config.initial_conditions import get_initial_conditions_asset_list
from fv3config._asset_list import write_asset
from .mocks import c12_config

TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

ASSET_LIST_EMPTY = []

required_run_directory_subdirectories = ["INPUT", "RESTART"]

required_base_forcing_filenames = ["forcing_file", "grb/grb_forcing_file"]

required_orographic_forcing_filenames = ["INPUT/orographic_file"]

required_default_initial_conditions_filenames = ["INPUT/initial_conditions_file"]

required_restart_initial_conditions_filenames = (
    ["INPUT/coupler.res"]
    + ["INPUT/fv_core.res.nc"]
    + [f"INPUT/fv_core.res.tile{n}.nc" for n in range(1, 7)]
    + [f"INPUT/fv_srf_wnd.res.tile{n}.nc" for n in range(1, 7)]
    + [f"INPUT/fv_tracer.res.tile{n}.nc" for n in range(1, 7)]
    + [f"INPUT/phy_data.tile{n}.nc" for n in range(1, 7)]
    + [f"INPUT/sfc_data.tile{n}.nc" for n in range(1, 7)]
)

additional_required_filenames = [
    "data_table",
    "diag_table",
    "field_table",
    "input.nml",
    "RESTART",
    "INPUT",
]

required_config_keys = [
    "namelist",
    "diag_table",
    "data_table",
    "forcing",
    "experiment_name",
    "initial_conditions",
]

gfs_initial_conditions_dir = os.path.join(
    "fv3config-cache", "initial_conditions", "gfs_initial_conditions"
)

restart_initial_conditions_dir = os.path.join(
    "fv3config-cache", "initial_conditions", "restart_initial_conditions"
)

option_abs_path = "/nonexistent/abs/path"
option_tag = "custom_option"

empty_built_in_options_dict = {}
one_item_built_in_options_dict = {"custom_option": "/path/to/custom/option"}


class ForcingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache_dir = tempfile.TemporaryDirectory()
        cls.original_cache_dir = fv3config.caching.get_cache_dir()
        fv3config.caching.set_cache_dir(cls.cache_dir.name)

    @classmethod
    def tearDownClass(cls):
        fv3config.caching.set_cache_dir(cls.original_cache_dir)
        cls.cache_dir.cleanup()

    def setUp(self):
        self._run_directory_list = []

    def tearDown(self):
        for directory in self._run_directory_list:
            directory.cleanup()

    def make_run_directory(self, directory_name):
        directory = tempfile.TemporaryDirectory(directory_name)
        self._run_directory_list.append(directory)
        return directory.name

    def test_write_default_base_forcing_directory(self):
        rundir = self.make_run_directory("test_rundir")
        config = c12_config()
        asset_list = get_base_forcing_asset_list(config)
        for asset in asset_list:
            write_asset(asset, rundir)
        self.assert_subpaths_present(rundir, required_base_forcing_filenames)

    def test_write_default_orographic_forcing_directory(self):
        rundir = self.make_run_directory("test_rundir")
        config = c12_config()
        asset_list = get_orographic_forcing_asset_list(config)
        for asset in asset_list:
            write_asset(asset, rundir)
        self.assert_subpaths_present(rundir, required_orographic_forcing_filenames)

    def test_zero_resolution_orographic_forcing_directory(self):
        config = {"namelist": {"fv_core_nml": {"npx": 0, "npy": 0}}}
        with self.assertRaises(fv3config.ConfigError):
            get_orographic_forcing_directory(config)

    def test_negative_resolution_orographic_forcing_directory(self):
        config = {"namelist": {"fv_core_nml": {"npx": -1, "npy": -1}}}
        with self.assertRaises(fv3config.ConfigError):
            get_orographic_forcing_directory(config)

    def test_empty_orographic_forcing_list(self):
        config = c12_config()
        config["orographic_forcing"] = []
        asset_list = get_orographic_forcing_asset_list(config)
        self.assertEqual(asset_list, ASSET_LIST_EMPTY)

    def test_write_default_initial_conditions_directory(self):
        rundir = self.make_run_directory("test_rundir")
        config = c12_config()
        asset_list = get_initial_conditions_asset_list(config)
        for asset in asset_list:
            write_asset(asset, rundir)
        self.assert_subpaths_present(
            rundir, required_default_initial_conditions_filenames
        )

    def test_get_specified_initial_conditions_directory(self):
        source_rundir = self.make_run_directory("source_rundir")
        config = c12_config()
        config["initial_conditions"] = source_rundir
        dirname = get_initial_conditions_directory(config)
        self.assertEqual(dirname, source_rundir)

    def test_get_bad_initial_conditions_directory(self):
        source_rundir = "/not/a/real/directory"
        config = c12_config()
        config["initial_conditions"] = source_rundir
        with self.assertRaises(fv3config.ConfigError):
            get_initial_conditions_directory(config)

    def test_get_specified_forcing_directory(self):
        source_rundir = self.make_run_directory("source_rundir")
        config = c12_config()
        config["forcing"] = source_rundir
        dirname = get_base_forcing_directory(config)
        self.assertEqual(dirname, source_rundir)

    def test_get_bad_forcing_directory(self):
        source_rundir = "/not/a/real/directory"
        config = c12_config()
        config["forcing"] = source_rundir
        with self.assertRaises(fv3config.ConfigError):
            get_base_forcing_directory(config)

    def test_write_default_run_directory(self):
        rundir = self.make_run_directory("test_rundir")
        config = c12_config()
        fv3config.write_run_directory(config, rundir)
        self.assert_subpaths_present(
            rundir,
            required_run_directory_subdirectories
            + required_default_initial_conditions_filenames
            + required_base_forcing_filenames
            + required_orographic_forcing_filenames
            + additional_required_filenames,
        )

    def test_write_run_directory_with_patch_file(self):
        sourcedir = self.make_run_directory("sourcedir")
        rundir = self.make_run_directory("test_rundir")
        config = c12_config()
        open(os.path.join(sourcedir, "empty_file"), "a").close()
        config["patch_files"] = {
            "source_location": sourcedir,
            "source_name": "empty_file",
            "target_location": "",
            "target_name": "empty_file",
            "copy_method": "copy",
        }
        fv3config.write_run_directory(config, rundir)
        self.assert_subpaths_present(
            rundir,
            required_run_directory_subdirectories
            + required_default_initial_conditions_filenames
            + required_base_forcing_filenames
            + required_orographic_forcing_filenames
            + additional_required_filenames
            + ["empty_file"],
        )

    def test_restart_directory_exists_and_empty(self):
        rundir = self.make_run_directory("test_rundir")
        restart_directory = os.path.join(rundir, "RESTART")
        config = c12_config()
        fv3config.write_run_directory(config, rundir)
        self.assertTrue(os.path.isdir(restart_directory))
        self.assertEqual(len(os.listdir(restart_directory)), 0)

    def test_default_config_has_required_keys(self):
        config = c12_config()
        self.assertTrue(set(required_config_keys) <= set(config.keys()))

    def assert_subpaths_present(self, dirname, subpath_list):
        missing_paths = []
        for subpath in subpath_list:
            path = os.path.join(dirname, subpath)
            if not os.path.exists(path):
                missing_paths.append(path)
        self.assertTrue(len(missing_paths) == 0, missing_paths)

    def test_resolve_option_abs_path(self):
        sample_abs_path = self.make_run_directory("sample_abs_path")
        self.assertEqual(
            resolve_option(sample_abs_path, empty_built_in_options_dict),
            sample_abs_path,
        )

    def test_resolve_option_nonexistent_abs_path(self):
        with self.assertRaises(fv3config.ConfigError):
            resolve_option(option_abs_path, empty_built_in_options_dict)

    def test_resolve_option_tag_empty_built_in_options(self):
        with self.assertRaises(fv3config.ConfigError):
            resolve_option(option_tag, empty_built_in_options_dict)

    def test_resolve_option_tag_proper_built_in_options(self):
        proper_option = one_item_built_in_options_dict[option_tag]
        self.assertEqual(
            resolve_option(option_tag, one_item_built_in_options_dict), proper_option
        )


if __name__ == "__main__":
    unittest.main()
