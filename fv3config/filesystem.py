import os
import shutil
from ._exceptions import DelayedImportError
from fsspec.implementations.local import LocalFileSystem
try:
    import gcsfs
except ImportError as err:
    gcsfs = DelayedImportError(err)
try:
    import google.auth
except ImportError as err:
    google = DelayedImportError(err)

LOCAL_FS = LocalFileSystem()
GS_BUCKET_PREFIX = 'gs://'


def _put_directory(local_source_dir, dest_dir, fs=None):
    """Copy the contents of a local directory to a local or remote directory.
    """
    if fs is None:
        fs = _get_fs(dest_dir)
    for token in os.listdir(local_source_dir):
        source = os.path.join(os.path.abspath(local_source_dir), token)
        dest = os.path.join(dest_dir, token)
        if os.path.isdir(source):
            fs.makedirs(dest, exist_ok=True)
            _put_directory(source, dest, fs)
        else:
            _put_file(source, dest, fs)


def _get_file(source_filename, dest_filename, fs=None):
    fs = _get_fs(source_filename)
    fs.get(source_filename, dest_filename)


def _put_file(source_filename, dest_filename, fs=None):
    fs = _get_fs(dest_filename)
    fs.put(source_filename, dest_filename)


def _is_gcloud_path(path):
    return path.startswith(GS_BUCKET_PREFIX)


def _get_gcloud_project():
    return os.environ.get(google.auth.environment_vars.PROJECT)


def _get_fs(path):
    if _is_gcloud_path(path):
        return _get_gcloud_fs()
    else:
        return LOCAL_FS


def _get_gcloud_fs():
    return gcsfs.GCSFileSystem(project=_get_gcloud_project())
