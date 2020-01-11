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
