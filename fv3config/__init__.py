# -*- coding: utf-8 -*-

"""Top-level package for fv3config."""

from .config import (
    config_to_namelist,
    config_from_namelist,
    get_default_config,
    write_run_directory,
    enable_restart,
    get_run_duration,
    set_run_duration,
    get_timestep,
    get_nudging_assets,
    enable_nudging,
    DiagTable,
    DiagFieldConfig,
    DiagFileConfig,
    Packing,
    FileFormat,
    dump,
    load,
)
from ._exceptions import InvalidFileError, ConfigError
from ._datastore import ensure_data_is_downloaded
from .fv3run import run_docker, run_native, run_kubernetes
from ._asset_list import (
    get_asset_dict,
    get_bytes_asset_dict,
    asset_list_from_path,
    write_asset,
)
from ._asset_list_config import config_to_asset_list
from .caching import CACHE_REMOTE_FILES, do_remote_caching, set_cache_dir, get_cache_dir


__author__ = """Allen Institute of Artificial Intelligence"""
__email__ = "jeremym@allenai.org"
__version__ = "0.9.0"

# necessary for auto-doc generation of API for public methods
__all__ = dir()
