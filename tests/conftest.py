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
DIAG_TABLE_PATH = "vcm-fv3config/config/diag_table/default/v1.0/diag_table"


def populate_mock_filesystem(fs):
    for filename in MOCK_FS_FILENAMES:

        parent_dir = os.path.dirname(filename)
        if not fs.exists(parent_dir):
            fs.mkdir(parent_dir)
        with fs.open(filename, mode="wb") as f:
            f.write(b"mock_data")
    with open(
        os.path.join(fv3config.data.DATA_DIR, "diag_table/diag_table_default"), "r"
    ) as f_in:
        with fs.open(DIAG_TABLE_PATH, "w") as f_out:
            f_out.write(f_in.read())


@pytest.fixture(autouse=True)
def mock_fs():
    memory_fs = MemoryFileSystem()
    populate_mock_filesystem(memory_fs)

    original_get_fs = fv3config.filesystem._get_fs

    def mock_get_fs(path: str) -> fsspec.AbstractFileSystem:
        """Return the fsspec filesystem required to handle a given path."""
        if path.startswith("memory://"):
            return memory_fs  # mock gs storage using a memory filesystem
        else:
            return original_get_fs(path)

    fv3config.filesystem._get_fs = mock_get_fs
    yield
    fv3config.filesystem._get_fs = original_get_fs


c12_config = pytest.fixture(mocks.c12_config)
