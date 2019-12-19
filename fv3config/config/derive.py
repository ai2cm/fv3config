import os
import re
from datetime import timedelta
from .._exceptions import ConfigError
from .._datastore import resolve_option
from ..data import DATA_DIR
from .default import NAMELIST_DEFAULTS


DATA_TABLE_OPTIONS = {
    "default": os.path.join(DATA_DIR, "data_table/data_table_default"),
}
DIAG_TABLE_OPTIONS = {
    "default": os.path.join(DATA_DIR, "diag_table/diag_table_default"),
    "no_output": os.path.join(DATA_DIR, "diag_table/diag_table_no_output"),
    "grid_spec": os.path.join(DATA_DIR, "diag_table/diag_table_grid_spec"),
}
FIELD_TABLE_OPTIONS = {
    "GFDLMP": os.path.join(DATA_DIR, "field_table/field_table_GFDLMP"),
    "ZhaoCarr": os.path.join(DATA_DIR, "field_table/field_table_ZhaoCarr"),
}


def get_n_processes(config):
    n_tiles = config["namelist"]["fv_core_nml"].get(
        "ntiles", NAMELIST_DEFAULTS["ntiles"]
    )
    layout = config["namelist"]["fv_core_nml"].get(
        "layout", NAMELIST_DEFAULTS["layout"]
    )
    processors_per_tile = layout[0] * layout[1]
    return n_tiles * processors_per_tile


def get_run_duration(config):
    """Return a timedelta indicating the duration of the run.

    Args:
        config (dict): a configuration dictionary

    Returns:
        duration (timedelta): the duration of the run

    Raises:
        ValueError: if the namelist contains a non-zero value for "months"
    """
    coupler_nml = config["namelist"].get("coupler_nml", {})
    months = coupler_nml.get("months", 0)
    if months != 0:  # months have no set duration and thus cannot be timedelta
        raise ValueError(f"namelist contains non-zero value {months} for months")
    return timedelta(
        **{
            name: coupler_nml.get(name, 0)
            for name in ("seconds", "minutes", "hours", "days")
        }
    )


def get_current_date(config, input_directory):
    """Return current_date from configuration dictionary and the local INPUT
    directory. The INPUT directory is passed in order to read current_date from
    any initial conditions files, since config can contain a remote data source
    and we do not want to download data in this function.

    Args:
        config (dict): a configuration dictionary
        input_directory (str): path to local INPUT directory

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    force_date_from_namelist = config["namelist"]["coupler_nml"].get(
        "force_date_from_namelist", False
    )
    # following code replicates the logic that the fv3gfs model uses to determine the current_date
    if force_date_from_namelist:
        current_date = config["namelist"]["coupler_nml"].get(
            "current_date", [0, 0, 0, 0, 0, 0]
        )
    else:
        coupler_res_filename = os.path.join(input_directory, "coupler.res")
        if os.path.exists(coupler_res_filename):
            current_date = _get_current_date_from_coupler_res(coupler_res_filename)
        else:
            current_date = config["namelist"]["coupler_nml"].get(
                "current_date", [0, 0, 0, 0, 0, 0]
            )
    return current_date


def get_microphysics_name(config):
    """Get name of microphysics scheme from configuration dictionary

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: name of microphysics scheme

    Raises:
        NotImplementedError: no microphysics name defined for specified
            imp_physics and ncld combination
    """
    imp_physics = config["namelist"]["gfs_physics_nml"].get("imp_physics")
    ncld = config["namelist"]["gfs_physics_nml"].get("ncld")
    if imp_physics == 11 and ncld == 5:
        microphysics_name = "GFDLMP"
    elif imp_physics == 99 and ncld == 1:
        microphysics_name = "ZhaoCarr"
    else:
        raise NotImplementedError(
            f"Microphysics choice imp_physics={imp_physics} and ncld={ncld} not one of the valid options"
        )
    return microphysics_name


def get_field_table_filename(config):
    """Get field_table filename given configuration dictionary

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: field_table filename

    Raises:
        NotImplementedError: if field_table for microphysics option specified
            in config has not been implemented
    """
    microphysics_name = get_microphysics_name(config)
    if microphysics_name in FIELD_TABLE_OPTIONS.keys():
        filename = FIELD_TABLE_OPTIONS[microphysics_name]
    else:
        raise NotImplementedError(
            f"Field table does not exist for {microphysics_name} microphysics"
        )
    return filename


def get_diag_table_filename(config):
    """Return filename for diag_table specified in config

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: diag_table filename
    """
    if "diag_table" not in config:
        raise ConfigError("config dictionary must have a 'diag_table' key")
    return resolve_option(config["diag_table"], DIAG_TABLE_OPTIONS)


def get_data_table_filename(config):
    """Return filename for data_table specified in config

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: data_table filename
    """
    if "data_table" not in config:
        raise ConfigError("config dictionary must have a 'data_table' key")
    return resolve_option(config["data_table"], DATA_TABLE_OPTIONS)


def _get_current_date_from_coupler_res(coupler_res_filename):
    """Return current_date specified in coupler.res file

    Args:
        coupler_res_filename (str): a coupler.res filename

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    with open(coupler_res_filename) as f:
        third_line = f.readlines()[2]
        current_date = [int(d) for d in re.findall(r"\d+", third_line)]
        if len(current_date) != 6:
            raise ConfigError(
                f"{coupler_res_filename} does not have a valid current model time (need six integers on third line)"
            )
    return current_date
