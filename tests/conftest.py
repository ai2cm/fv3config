import pytest
import os
import fsspec
from fsspec.implementations.memory import MemoryFileSystem
import fv3config.filesystem
import fv3config.data
from . import mocks

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

MOCK_FS_FILENAMES = [
    "vcm-fv3config/data/initial_conditions/gfs_c12_example/v1.0/initial_conditions_file",
    "vcm-fv3config/data/base_forcing/v1.1/forcing_file",
    "vcm-fv3config/data/base_forcing/v1.1/grb/grb_forcing_file",
    "vcm-fv3config/data/orographic_data/v1.0/C12/orographic_file",
    "vcm-fv3config/data/gfs_nudging_data/v1.0/20160801_00.nc",
    "vcm-fv3config/data/gfs_nudging_data/v1.0/20160801_06.nc",
]
DIAG_TABLE_PATH = "gs://vcm-fv3config/config/diag_table/default/v1.0/diag_table"


def populate_mock_filesystem(fs):
    for filename in MOCK_FS_FILENAMES:
        fs.mkdir(os.path.dirname(filename))
        with fs.open(filename, mode="wb") as f:
            f.write(b"mock_data")
    with open(
        os.path.join(fv3config.data.DATA_DIR, "diag_table/diag_table_default"), "r"
    ) as f_in:
        with fs.open(DIAG_TABLE_PATH, "w") as f_out:
            f_out.write(f_in.read())


class MockGCSFileSystem(MemoryFileSystem):

    protocol = "gcs", "gs"

    def ls(self, path, recursive=False, **kwargs):
        path = self._strip_protocol(path)
        return super().ls(path, **kwargs)

    def mkdir(self, path, create_parents=True, **kwargs):
        path = self._strip_protocol(path)
        return super().mkdir(path, create_parents, **kwargs)

    def rmdir(self, path, *args, **kwargs):
        path = self._strip_protocol(path)
        return super().rmdir(path, *args, **kwargs)

    def exists(self, path):
        path = self._strip_protocol(path)
        return path in self.store or path in self.pseudo_dirs

    def open(self, path, *args, **kwargs):
        path = self._strip_protocol(path)
        return super().open(path, *args, **kwargs)


@pytest.fixture(autouse=True)
def mock_gs_fs():
    memory_fs = MockGCSFileSystem()
    populate_mock_filesystem(memory_fs)

    def mock_get_fs(path: str) -> fsspec.AbstractFileSystem:
        """Return the fsspec filesystem required to handle a given path."""
        if path.startswith("gs://"):
            return memory_fs  # mock gs storage using a memory filesystem
        else:
            return fsspec.filesystem("file")

    _get_fs, fv3config.filesystem._get_fs = fv3config.filesystem._get_fs, mock_get_fs
    yield
    fv3config.filesystem._get_fs = _get_fs


c12_config = pytest.fixture(mocks.c12_config)
