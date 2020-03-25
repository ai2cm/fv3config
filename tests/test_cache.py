import unittest
import tempfile
import pytest
import fv3config
import os
import shutil


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


class CacheDirectoryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cache_dir = tempfile.TemporaryDirectory()
        cls.original_cache_dir = fv3config.caching.get_cache_dir()
        fv3config.caching.set_cache_dir(cls.cache_dir.name)
        fv3config.ensure_data_is_downloaded()

    @classmethod
    def tearDownClass(cls):
        fv3config.caching.set_cache_dir(cls.original_cache_dir)
        cls.cache_dir.cleanup()

    def tearDown(self):
        gs_cache_dir = os.path.join(
            self.cache_dir.name,
            "fv3config-cache/gs/"
        )
        if os.path.isdir(gs_cache_dir):
            shutil.rmtree(gs_cache_dir)

    def test_cache_diag_table(self):
        config = fv3config.get_default_config()
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
        config = fv3config.get_default_config()
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
        config = fv3config.get_default_config()
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
        config = fv3config.get_default_config()
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
