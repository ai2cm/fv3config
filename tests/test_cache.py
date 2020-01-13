import unittest
import tempfile
import pytest
import fv3config
import os


@pytest.mark.parametrize(
    "source_filename, cache_subpath",
    [
        ("gs://my-bucket/my_filename.txt", "gs/my-bucket/my_filename.txt"),
        ("http://www.mysite.com/dir/file.nc", "http/www.mysite.com/dir/file.nc"),
    ],
)
def test_cache_filename(source_filename, cache_subpath):
    cache_dir = fv3config.filesystem.get_internal_cache_dir()
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
        cls.original_cache_dir = fv3config.cache_location.get_cache_dir()
        fv3config.cache_location.set_cache_dir(cls.cache_dir.name)
        fv3config.ensure_data_is_downloaded()

    @classmethod
    def tearDownClass(cls):
        fv3config.cache_location.set_cache_dir(cls.original_cache_dir)
        cls.cache_dir.cleanup()

    def test_cache_diag_table(self):
        config = fv3config.get_default_config()
        config['diag_table'] = 'gs://vcm-fv3config/config/diag_table/default/v1.0/diag_table'
        with tempfile.TemporaryDirectory() as rundir:
            fv3config.write_run_directory(config, rundir)
        assert os.path.isfile(
            os.path.join(
                fv3config.get_cache_dir(),
                'fv3config-cache/gs/vcm-fv3config/config/diag_table/default/v1.0/diag_table'
            )
        )
