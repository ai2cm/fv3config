import collections
import unittest
import tempfile
import pytest
import fv3config
import os
import shutil
import copy
import datetime

from .mocks import c12_config

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


DEFAULT_CONFIG = c12_config()


def update_recursive(base, update):
    for k, v in update.items():
        if isinstance(v, collections.abc.Mapping):
            base[k] = update_recursive(base.get(k, {}), v)
        else:
            base[k] = v
    return base


@pytest.mark.parametrize(
    "source_filename, cache_subpath",
    [
        ("gs://my-bucket/my_filename.txt", "gs/my-bucket/my_filename.txt"),
        ("http://www.mysite.com/dir/file.nc", "http/www.mysite.com/dir/file.nc"),
    ],
)
def test_cache_filename(source_filename, cache_subpath):
    cache_dir = fv3config.caching.get_internal_cache_dir()
    cache_filename = os.path.join(cache_dir, cache_subpath)
    result = fv3config.filesystem._get_cache_filename(source_filename)
    assert result == cache_filename


def test_cache_filename_raises_on_no_filename():
    with pytest.raises(ValueError):
        fv3config.filesystem._get_cache_filename("gs://")


class ChangeCacheDirectoryTests(unittest.TestCase):
    def test_get_archive_dir(self):
        result = fv3config.caching.get_cache_dir()
        assert isinstance(result, str)
        assert os.path.isabs(result)

    def test_set_then_get_archive_dir(self):
        with tempfile.TemporaryDirectory() as tempdir:
            original = fv3config.caching.get_cache_dir()
            try:
                fv3config.caching.set_cache_dir(tempdir)
                new = fv3config.caching.get_cache_dir()
                assert new != original
                assert new == tempdir
            finally:
                fv3config.caching.set_cache_dir(original)


class CacheDirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache_dir = tempfile.TemporaryDirectory()
        cls.original_cache_dir = fv3config.caching.get_cache_dir()
        fv3config.caching.set_cache_dir(cls.cache_dir.name)

    @classmethod
    def tearDownClass(cls):
        fv3config.caching.set_cache_dir(cls.original_cache_dir)
        cls.cache_dir.cleanup()

    def tearDown(self):
        gs_cache_dir = os.path.join(self.cache_dir.name, "fv3config-cache/gs/")
        if os.path.isdir(gs_cache_dir):
            shutil.rmtree(gs_cache_dir)

    def test_cache_diag_table(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config[
            "diag_table"
        ] = "gs://vcm-fv3config/config/diag_table/default/v1.0/diag_table"
        cache_filename = os.path.join(
            fv3config.get_cache_dir(),
            "fv3config-cache/gs/vcm-fv3config/config/diag_table/default/v1.0/diag_table",
        )
        assert not os.path.isfile(cache_filename)
        with tempfile.TemporaryDirectory() as rundir:
            fv3config.write_run_directory(config, rundir)
        assert os.path.isfile(cache_filename)

    def test_disable_caching(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config[
            "diag_table"
        ] = "gs://vcm-fv3config/config/diag_table/default/v1.0/diag_table"
        cache_filename = os.path.join(
            fv3config.get_cache_dir(),
            "fv3config-cache/gs/vcm-fv3config/config/diag_table/default/v1.0/diag_table",
        )
        assert not os.path.isfile(cache_filename)
        fv3config.do_remote_caching(False)
        with tempfile.TemporaryDirectory() as rundir:
            fv3config.write_run_directory(config, rundir)
        assert not os.path.isfile(cache_filename)

    def test_reenable_caching(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config[
            "diag_table"
        ] = "gs://vcm-fv3config/config/diag_table/default/v1.0/diag_table"
        cache_filename = os.path.join(
            fv3config.get_cache_dir(),
            "fv3config-cache/gs/vcm-fv3config/config/diag_table/default/v1.0/diag_table",
        )
        assert not os.path.isfile(cache_filename)
        fv3config.do_remote_caching(False)
        fv3config.do_remote_caching(True)
        with tempfile.TemporaryDirectory() as rundir:
            fv3config.write_run_directory(config, rundir)
        assert os.path.isfile(cache_filename)

    def test_cached_diag_table_is_not_redownloaded(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config[
            "diag_table"
        ] = "gs://vcm-fv3config/config/diag_table/default/v1.0/diag_table"
        with tempfile.TemporaryDirectory() as rundir:
            fv3config.write_run_directory(config, rundir)
        cache_filename = os.path.join(
            fv3config.get_cache_dir(),
            "fv3config-cache/gs/vcm-fv3config/config/diag_table/default/v1.0/diag_table",
        )
        assert os.path.isfile(cache_filename)
        modification_time = os.path.getmtime(cache_filename)
        with tempfile.TemporaryDirectory() as rundir:
            fv3config.write_run_directory(config, rundir)
        assert os.path.getmtime(cache_filename) == modification_time


def test_rundir_contains_fv3config_yml():
    config = c12_config()
    with tempfile.TemporaryDirectory() as rundir:
        fv3config.write_run_directory(config, rundir)
        assert "fv3config.yml" in os.listdir(rundir)


def test_write_run_directory_succeeds_with_diag_table_class():
    config = c12_config()
    start_time = datetime.datetime(2000, 1, 1)
    config["diag_table"] = fv3config.DiagTable("name", start_time, [])
    with tempfile.TemporaryDirectory() as rundir:
        fv3config.write_run_directory(config, rundir)


def test_rundir_contains_nudging_asset_if_enabled():
    config = c12_config()
    config["gfs_analysis_data"] = {
        "url": "memory://vcm-fv3config/data/gfs_nudging_data/v1.0",
        "filename_pattern": "%Y%m%d_%H.nc",
    }
    config["namelist"]["fv_core_nml"]["nudge"] = True
    with tempfile.TemporaryDirectory() as rundir:
        fv3config.write_run_directory(config, rundir)
        assert "20160801_00.nc" in os.listdir(os.path.join(rundir, "INPUT"))
        assert "20160801_06.nc" in os.listdir(os.path.join(rundir, "INPUT"))


@pytest.mark.parametrize(
    "config_update",
    [
        {},
        {
            "gfs_analysis_data": {
                # these urls are hardcoded in tests/conftest.py and tests/mocks.py
                "url": "memory://vcm-fv3config/data/gfs_nudging_data/v1.0",
                "filename_pattern": "%Y%m%d_%H.nc",
            },
            "namelist": {"fv_core_nml": {"nudge": True}},
        },
        {
            "initial_conditions": [
                fv3config.get_asset_dict(
                    # these urls are hardcoded in tests/conftest.py and tests/mocks.py
                    "memory://vcm-fv3config/data/initial_conditions/gfs_c12_example/v1.0",
                    "initial_conditions_file",
                    target_location="explicit",
                )
            ]
        },
    ],
)
def test_write_run_directory_does_not_mutate_config(config_update):
    config = c12_config()
    config = update_recursive(config, config_update)
    config_copy = copy.deepcopy(config)
    with tempfile.TemporaryDirectory() as rundir:
        fv3config.write_run_directory(config, rundir)
        assert config == config_copy
