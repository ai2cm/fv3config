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


def _copy_directory(local_source_dir, dest_dir, fs=None):
    """Copy the contents of a local directory to a local or remote directory.
    """
    if fs is None:
        fs = _get_fs(dest_dir)
    for token in os.listdir(local_source_dir):
        source = os.path.join(os.path.abspath(local_source_dir), token)
        dest = os.path.join(dest_dir, token)
        if os.path.isdir(source):
            fs.makedirs(dest, exist_ok=True)
            _copy_directory(source, dest, fs)
        else:
            _copy_file(source, dest, fs)


def _copy_file(source_filename, dest_filename, fs=None):
    """Copy a local or remote file to a local or remote target location."""
    if fs is None and (_is_gcloud_path(source_filename) or _is_gcloud_path(dest_filename)):
        fs = _get_gcloud_fs()
    if not _is_gcloud_path(source_filename):
        if not _is_gcloud_path(dest_filename):
            shutil.copy2(source_filename, dest_filename, follow_symlinks=True)
        else:
            fs.put(source_filename, dest_filename)
    else:  # source is remote
        if not _is_gcloud_path(dest_filename):
            fs.get(source_filename, dest_filename)
        else:
            raise NotImplementedError('Cannot copy from Google cloud to Google cloud')


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
