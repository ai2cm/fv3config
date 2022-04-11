import os
import pathlib
import fsspec
import re
from ._exceptions import DelayedImportError
from . import caching
from concurrent.futures import ThreadPoolExecutor, Executor


try:
    import google.auth
except ImportError as err:
    google = DelayedImportError(err)


def get_fs(path: str) -> fsspec.AbstractFileSystem:
    """Return the fsspec filesystem required to handle a given path."""
    return _get_fs(path)


def _get_fs(path: str) -> fsspec.AbstractFileSystem:
    """Private function implementing public get_fs function, used so that if we
    mock this implementation, it is still used in modules which import using
    `from filesystem import get_fs`.
    """
    protocol = _Location(path).get_protocol()
    return fsspec.filesystem(protocol)


def isabs(path: str) -> bool:
    """Return whether the path is a local or remote absolute path"""
    if len(_get_protocol_prefix(path)) > 0:
        return True
    else:  # local file
        return os.path.isabs(path)


def is_existing_absolute_path(path: str) -> bool:
    """Return whether the path is an existing absolute path"""
    return isabs(path) and get_fs(path).exists(path)


class _Location:
    def __init__(self, location: str) -> None:
        self.match = re.match(r"(?P<prefix>(?P<protocol>.*?)://)?", location)
        if self.match is None:
            raise ValueError(f"protocol could not be inferred from {location}")

    def get_protocol(self) -> str:
        return self.match.group("protocol") or "file"

    def get_protocol_prefix(self) -> str:
        return self.match.group("prefix") or ""


def _get_protocol_prefix(location):
    """If a string starts with "<protocol>://"", return that part of the string.
    Otherwise, return an empty string.
    """
    return _Location(location).get_protocol_prefix()


def _get_path(location):
    """If a string starts with "<protocol>://"", return the rest of the string.
    Otherwise, return the entire string.
    """
    separator = "://"
    if separator in location:
        return location[location.index(separator) + len(separator) :]
    else:
        return location


def is_local_path(location):
    """returns True if the location is local, False otherwise"""
    return _get_protocol_prefix(location) == ""


def walk_safe(fs, location):
    """Some fsspec implementations have a bug where they return an empty string
    as one of the files
    """
    for dirpath, dirnames, files in fs.walk(location):
        files = [f for f in files if f]
        yield dirpath, dirnames, files


def put_directory(
    local_source_dir: str,
    dest_dir: str,
    fs: fsspec.AbstractFileSystem = None,
    executor: Executor = None,
):
    """Copy the contents of a local directory to a local or remote directory.
    """
    if fs is None:
        fs = get_fs(dest_dir)
    if executor is None:
        executor = ThreadPoolExecutor()
        manage_threads = True
    else:
        manage_threads = False
    for token in os.listdir(local_source_dir):
        source = os.path.join(os.path.abspath(local_source_dir), token)
        dest = os.path.join(dest_dir, token)
        if os.path.isdir(source):
            fs.makedirs(dest, exist_ok=True)  # must be blocking call
            put_directory(source, dest, fs=fs, executor=executor)
        else:
            executor.submit(fs.put, source, dest)
    if manage_threads:
        executor.shutdown(wait=True)


def get_file(source_filename: str, dest_filename: str, cache: bool = None):
    """Copy a file from a local or remote location to a local location.

    Optionally cache remote files in the local fv3config cache.
    
    Args:
        source_filename: the local or remote location to copy
        dest_filename: the local target location
        cache (optional): if True and source is remote, copy the file from the
            fv3config cache if it has been previously downloaded, and cache the file
            if not. Does nothing if source_filename is local.
            Default ``fv3config.caching.CACHE_REMOTE_FILES``, set by
            ``fv3config.enable_remote_caching(True/False)``.
    """
    if cache is None:
        cache = caching.CACHE_REMOTE_FILES
    if not cache or is_local_path(source_filename):
        _get_file_uncached(source_filename, dest_filename)
    else:
        _get_file_cached(source_filename, dest_filename)


def _get_file_uncached(source_filename, dest_filename):
    fs = get_fs(source_filename)
    fs.get(source_filename, dest_filename)


def _get_file_cached(source_filename, dest_filename):
    if is_local_path(source_filename):
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
    path_str: str = _get_path(source_filename)
    if len(path_str) == 0:
        raise ValueError(f"no file path given in source filename {source_filename}")
    # if path starts with / then it will break the cache:
    # cache_path//a becomes /a with posix paths
    path = pathlib.Path(path_str)
    cache_dir = pathlib.Path(caching.get_internal_cache_dir()).absolute()

    if path.is_absolute():
        path_no_root = path.relative_to(path.root)
        cache_label = "abs"
    else:
        path_no_root = path
        cache_label = "rel"
    path_in_cache = cache_dir / cache_label / prefix / path_no_root
    return path_in_cache.as_posix()


open = fsspec.open
