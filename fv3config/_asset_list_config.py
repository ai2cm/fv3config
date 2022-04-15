"""Routines for converting an fv3config dict into a list of assets

"""
import io
import os

from ._datastore import (
    get_orographic_forcing_directory,
    get_base_forcing_directory,
)
from fv3config._datastore import (
    get_field_table_filename,
    get_diag_table_filename,
    get_data_table_filename,
)
from .config.diag_table import DiagTable
from .config.namelist import config_to_namelist
from .config._serialization import dump
from fv3config.config.initial_conditions import get_initial_conditions_asset_list
from . import filesystem
from ._asset_list import (
    is_dict_or_list,
    ensure_is_list,
    get_asset_dict,
    get_bytes_asset_dict,
    get_patch_file_assets,
    asset_list_from_path,
)

FV3CONFIG_YML_NAME = "fv3config.yml"


def get_orographic_forcing_asset_list(config):
    """Return asset_list for orographic forcing"""
    if is_dict_or_list(config["orographic_forcing"]):
        return ensure_is_list(config["orographic_forcing"])
    else:
        source_directory = get_orographic_forcing_directory(config)
        return asset_list_from_path(
            source_directory, target_location="INPUT", copy_method="link"
        )


def get_base_forcing_asset_list(config):
    """Return asset_list for base forcing"""
    if is_dict_or_list(config["forcing"]):
        return ensure_is_list(config["forcing"])
    else:
        source_directory = get_base_forcing_directory(config)
        return asset_list_from_path(source_directory, copy_method="link")


def get_data_table_asset(config):
    """Return asset for data_table"""
    data_table_filename = get_data_table_filename(config)
    location, name = os.path.split(data_table_filename)
    return get_asset_dict(location, name, target_name="data_table")


def get_diag_table_asset(config):
    """Return asset for diag_table"""
    if isinstance(config["diag_table"], DiagTable):
        data = bytes(str(config["diag_table"]), "UTF-8")
    else:
        # TODO remove I/O from to top level
        diag_table_filename = get_diag_table_filename(config)
        data = filesystem.cat(diag_table_filename)
    return get_bytes_asset_dict(data, ".", "diag_table")


def get_field_table_asset(config):
    """Return asset for field_table"""
    field_table_filename = get_field_table_filename(config)
    location, name = os.path.split(field_table_filename)
    return get_asset_dict(location, name, target_name="field_table")


def get_fv3config_yaml_asset(config):
    """An asset containing this configuration"""
    f = io.StringIO()
    dump(config, f)
    return get_bytes_asset_dict(
        bytes(f.getvalue(), "UTF-8"),
        target_location=".",
        target_name=FV3CONFIG_YML_NAME,
    )


def config_to_asset_list(config):
    """Convert a configuration dictionary to an asset list. The asset list
    will contain all files for the run directory except the namelist."""
    asset_list = []
    asset_list += get_initial_conditions_asset_list(config)
    asset_list += get_base_forcing_asset_list(config)
    asset_list += get_orographic_forcing_asset_list(config)
    asset_list.append(get_field_table_asset(config))
    asset_list.append(get_diag_table_asset(config))
    asset_list.append(get_data_table_asset(config))
    asset_list.append(get_fv3config_yaml_asset(config))
    asset_list.append(get_namelist_asset(config))
    asset_list.extend(get_patch_file_assets(config))
    return asset_list


def get_namelist_asset(config):
    text = config_to_namelist(config)
    data = text.encode()
    return get_bytes_asset_dict(data, target_location="", target_name="input.nml")
