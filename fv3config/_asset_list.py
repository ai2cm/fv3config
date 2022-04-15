"""Assets

Assets represent either remote, local, or in memory data that can be written to
a local disk
"""
import logging
import os

from ._exceptions import ConfigError
from . import filesystem


logger = logging.getLogger("fv3config")


def is_dict_or_list(option):
    return isinstance(option, dict) or isinstance(option, list)


def ensure_is_list(asset):
    """If argument is a dict, return length 1 list containing dict"""
    if isinstance(asset, dict):
        return [asset]
    elif isinstance(asset, list):
        return asset
    else:
        raise ConfigError("Asset must be a dict or list of dicts")


def get_asset_dict(
    source_location,
    source_name,
    target_location="",
    target_name=None,
    copy_method="copy",
):
    """Helper function to generate asset for a particular file

    Args:
        source_location (str): path to directory containing source file
        source_name (str): filename of source file
        target_location (str, optional): sub-directory to which file will
            be written, relative to run directory root. Defaults to empty
            string (i.e. root of run directory).
        target_name (str, optional): filename to which file will be written.
            Defaults to None, in which case source_name is used.
        copy_method (str, optional): flag to determine whether file is
            copied ('copy') or hard-linked ('link'). Defaults to 'copy'.

    Returns:
        dict: an asset dictionary
    """
    if not source_name:
        raise ValueError(f"'{source_name}' cannot be an empty string.")

    if target_name is None:
        target_name = source_name
    asset = {
        "source_location": source_location,
        "source_name": source_name,
        "target_location": target_location,
        "target_name": target_name,
        "copy_method": copy_method,
    }
    return asset


def get_bytes_asset_dict(
    data: bytes, target_location: str, target_name: str,
):
    """Helper function to define the necessary fields for a binary asset to
    be saved at a given location.

    Args:
        data: the bytes to save
        target_location: sub-directory to which file will
            be written, relative to run directory root. Defaults to empty
            string (i.e. root of run directory).
        target_name: filename to which file will be written.
            Defaults to None, in which case source_name is used.

    Returns:
        dict: an asset dictionary
    """

    return {
        "bytes": data,
        "target_location": target_location,
        "target_name": target_name,
    }


def get_directory_asset_dict(path: str):
    """An asset representing an empty folder to be created

    Args:
       path: the directory to create relative to the rundir root
    """
    return {"target_name": "", "target_location": path, "directory": True}


def _without_dot(path):
    if path == ".":
        return ""
    else:
        return path


def asset_list_from_path(from_location, target_location="", copy_method="copy"):
    """Return asset_list from all files within a given path.

    Args:
        location (str): local path or google cloud storage url.
        target_location (str, optional): target_location used for generated assets.
            Defaults to '' which is root of run-directory.
        copy_method ('copy' or 'link', optional): whether to copy or link assets,
            defaults to 'copy'. If location is a google cloud storage url, this option
            is ignored and files are copied.

    Returns:
        list: a list of asset dictionaries
        """
    if not filesystem.is_local_path(from_location):
        copy_method = "copy"
    asset_list = []
    for dirname, basename, relative_target_location in _asset_walk(from_location):
        asset_list.append(
            get_asset_dict(
                dirname,
                basename,
                target_location=os.path.join(target_location, relative_target_location),
                copy_method=copy_method,
            )
        )
    return asset_list


def _asset_walk(location):
    fs = filesystem.get_fs(location)
    protocol_prefix = filesystem._get_protocol_prefix(location)
    for dirname, _, files in filesystem.walk_safe(fs, location):
        dirname = protocol_prefix + dirname
        subdir_target_location = os.path.relpath(dirname, start=location)
        for basename in files:
            yield dirname, basename, _without_dot(subdir_target_location)


def write_asset(asset, target_directory):
    """Write file represented by asset to target_directory

    Args:
        asset (dict): an asset dict
        target_directory (str): path to a directory in which all files will be written
    """

    target_path = os.path.join(
        target_directory, asset["target_location"], asset["target_name"]
    )

    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    if "copy_method" in asset:
        copy_file_asset(asset, target_path)
    elif "bytes" in asset:
        logger.debug(f"Writing asset bytes to {target_path}.")
        with open(target_path, "wb") as f:
            f.write(asset["bytes"])
    elif "directory" in asset:
        return os.makedirs(target_path, exist_ok=True)
    else:
        raise ConfigError(
            "Cannot write asset. Asset must have either a `copy_method` or `bytes` key."
        )


def copy_file_asset(asset, target_path):
    check_asset_has_required_keys(asset)
    source_path = os.path.join(asset["source_location"], asset["source_name"])
    copy_method = asset["copy_method"]
    if copy_method == "copy":
        logger.debug(f"Copying asset from {source_path} to {target_path}.")
        filesystem.get_file(source_path, target_path)
    elif copy_method == "link":
        logger.debug(f"Linking asset from {source_path} to {target_path}.")
        link_file(source_path, target_path)
    else:
        raise ConfigError(
            f"Behavior of copy_method {copy_method} not defined for {source_path} asset"
        )


def check_asset_has_required_keys(asset):
    """Check asset has all of its required keys"""
    required_asset_keys = [
        "source_location",
        "source_name",
        "target_location",
        "target_name",
        "copy_method",
    ]
    for required_asset_key in required_asset_keys:
        if required_asset_key not in asset:
            raise ConfigError(f"Assets must have a {required_asset_key}")


def link_file(source_item, target_item):
    if any(not filesystem.is_local_path(item) for item in [source_item, target_item]):
        raise NotImplementedError(
            "cannot perform linking operation involving remote urls "
            f"from {source_item} to {target_item}"
        )
    if os.path.exists(target_item):
        os.remove(target_item)
    os.symlink(source_item, target_item)


def get_patch_file_assets(config):
    if "patch_files" in config:
        if is_dict_or_list(config["patch_files"]):
            yield from ensure_is_list(config["patch_files"])
        else:
            raise ConfigError(
                "patch_files item in config dictionary must be an asset dict or "
                "list of asset dicts"
            )
