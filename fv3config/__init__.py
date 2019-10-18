# -*- coding: utf-8 -*-

"""Top-level package for FV3Config."""

from .config import (
    config_dict_to_namelist, config_dict_from_namelist, config_dict_from_directory, get_default_config_dict,
    write_run_directory,
)
from .exceptions import InvalidFileError, ConfigError
from .datastore import (
    get_initial_conditions_directory, get_base_forcing_directory, get_orographic_forcing_directory,
    link_directory, get_field_table_filename, get_diag_table_filename,
)

__all__ = [
    config_dict_to_namelist, config_dict_from_namelist, config_dict_from_directory, get_default_config_dict,
    write_run_directory,
    InvalidFileError, ConfigError,
    get_base_forcing_directory, get_orographic_forcing_directory, link_directory,
    get_field_table_filename, get_diag_table_filename,
]

__author__ = """Vulcan Technologies, LLC"""
__email__ = 'jeremym@vulcan.com'
__version__ = '0.1.0'
