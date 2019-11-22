import unittest
import requests
import tempfile
import tarfile
import fv3config
import os

TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
TAR_GZ_FILENAME = os.path.join(
    TEST_DIRECTORY, 'testdata/2019-10-23-data-for-running-fv3gfs.tar.gz'
)


class MockResponse(object):

    times_called = 0

    @property
    def content(self):
        MockResponse.times_called += 1
        with open(TAR_GZ_FILENAME, mode='rb') as tarfile:
            return tarfile.read()


def mock_requests_get(url):
    return MockResponse()


FILENAME = 'mock_file'
FILE_CONTENT = 'mock_content\n'


class DatastoreTests(unittest.TestCase):

    def test_get_archive_dir(self):
        result = fv3config.get_cache_dir()
        assert isinstance(result, str)
        assert os.path.isabs(result)

    def test_set_then_get_archive_dir(self):
        with tempfile.TemporaryDirectory() as tempdir:
            original = fv3config.get_cache_dir()
            try:
                fv3config.set_cache_dir(tempdir)
                new = fv3config.get_cache_dir()
                assert new != original
                assert new == tempdir
            finally:
                fv3config.set_cache_dir(original)


class DatastoreFileTests(unittest.TestCase):

    def setUp(self):
        self._original_get = requests.get
        requests.get = mock_requests_get
        self._cachedir_obj = tempfile.TemporaryDirectory()
        self.cachedir = self._cachedir_obj.name
        self.original_cachedir = fv3config.get_cache_dir()
        fv3config.set_cache_dir(self.cachedir)
        MockResponse.times_called = 0

    def tearDown(self):
        requests.get = self._original_get
        fv3config.set_cache_dir(self.original_cachedir)
        self._cachedir_obj.cleanup()

    def test_ensure_data_is_downloaded_when_empty(self):
        assert len(os.listdir(self.cachedir)) == 0
        fv3config.ensure_data_is_downloaded()
        filename_list = os.listdir(self.cachedir)
        assert len(filename_list) == 1
        assert filename_list[0] == FILENAME
        with open(os.path.join(self.cachedir, FILENAME), 'r') as f:
            assert f.read() == FILE_CONTENT

    def test_data_is_not_redownloaded(self):
        assert MockResponse.times_called == 0
        assert len(os.listdir(self.cachedir)) == 0
        fv3config.ensure_data_is_downloaded()
        assert MockResponse.times_called == 1
        assert len(os.listdir(self.cachedir)) == 1
        fv3config.ensure_data_is_downloaded()
        assert MockResponse.times_called == 1

    def test_redownload_will_redownload(self):
        assert MockResponse.times_called == 0
        assert len(os.listdir(self.cachedir)) == 0
        fv3config.ensure_data_is_downloaded()
        assert MockResponse.times_called == 1
        assert len(os.listdir(self.cachedir)) == 1
        fv3config._datastore.refresh_downloaded_data()
        assert MockResponse.times_called == 2
        assert len(os.listdir(self.cachedir)) == 1
