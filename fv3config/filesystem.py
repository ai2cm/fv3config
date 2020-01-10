import os
import fsspec
from ._exceptions import DelayedImportError

try:
    import gcsfs
except ImportError as err:
    gcsfs = DelayedImportError(err)
try:
    import google.auth
except ImportError as err:
    google = DelayedImportError(err)


def get_fs(path: str) -> fsspec.AbstractFileSystem:
    """Return the fsspec filesystem required to handle a given path."""
    if path.startswith("gs://"):
        return fsspec.filesystem("gs")
    else:
        return fsspec.filesystem("file")


def isabs(path: str) -> bool:
    """Return whether the path is a local or remote absolute path"""
    if len(_get_protocol_prefix(path)) > 0:
        return True
    else:  # local file
        return os.path.isabs(path)


def _get_protocol_prefix(location):
    """If a string starts with "<protocol>://"", return that part of the string.
    Otherwise, return an empty string.
    """
    separator = "://"
    if separator in location:
        return location[: location.index(separator) + len(separator)]
    else:
        return ""


def _is_local_path(location):
    return _get_protocol_prefix(location) == ""


def _put_directory(local_source_dir, dest_dir, fs=None):
    """Copy the contents of a local directory to a local or remote directory.
    """
    if fs is None:
        fs = get_fs(dest_dir)
    for token in os.listdir(local_source_dir):
        source = os.path.join(os.path.abspath(local_source_dir), token)
        dest = os.path.join(dest_dir, token)
        if os.path.isdir(source):
            fs.makedirs(dest, exist_ok=True)
            _put_directory(source, dest, fs)
        else:
            fs.put(source, dest)


def _get_file(source_filename, dest_filename):
    fs = get_fs(source_filename)
    fs.get(source_filename, dest_filename)


def _put_file(source_filename, dest_filename):
    fs = get_fs(dest_filename)
    fs.put(source_filename, dest_filename)
