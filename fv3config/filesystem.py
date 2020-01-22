import os
import fsspec
import gcsfs
from ._exceptions import DelayedImportError
from .cache_location import get_internal_cache_dir

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
        fs = gcsfs.GCSFileSystem(token=None)
        fs.connect()
        return fs
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


def _get_path(location):
    """If a string starts with "<protocol>://"", return the rest of the string.
    Otherwise, return the entire string.
    """
    separator = "://"
    if separator in location:
        return location[location.index(separator) + len(separator) :]
    else:
        return location


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


def get_file(source_filename, dest_filename, cache=False):
    """Copy a file from a local or remote location to a local location.

    Optionally cache remote files in the local fv3config cache.
    
    Args:
        source_filename (str): the local or remote location to copy
        dest_filename (str): the local target location
        cache (bool, optional): if True and source is remote, copy the file from the
            fv3config cache if it has been previously downloaded, and cache the file
            if not. Does nothing if source_filename is local. Default is False.
    """
    if not cache or _is_local_path(source_filename):
        _get_file_uncached(source_filename, dest_filename)
    else:
        _get_file_cached(source_filename, dest_filename)


def _get_file_uncached(source_filename, dest_filename):
    fs = get_fs(source_filename)
    fs.get(source_filename, dest_filename)


def _get_file_cached(source_filename, dest_filename):
    if _is_local_path(source_filename):
        raise ValueError(f"will not cache a local path, was given {source_filename}")
    else:
        cache_location = _get_cache_filename(source_filename)
        if not os.path.isfile(cache_location):
            os.makedirs(os.path.dirname(cache_location), exist_ok=True)
            _get_file_uncached(source_filename, cache_location)
        _get_file_uncached(cache_location, dest_filename)


def put_file(source_filename, dest_filename):
    """Copy a file from a local location to a local or remote location.
    
    Args:
        source_filename (str): the local location to copy
        dest_filename (str): the local or remote target location
    """
    fs = get_fs(dest_filename)
    fs.put(source_filename, dest_filename)


def _get_cache_filename(source_filename):
    prefix = _get_protocol_prefix(source_filename).strip("://")
    path = _get_path(source_filename)
    if len(path) == 0:
        raise ValueError(f"no file path given in source filename {source_filename}")
    cache_dir = get_internal_cache_dir()
    return os.path.join(cache_dir, prefix, path)
