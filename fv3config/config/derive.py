import os
import re
from datetime import timedelta
from .._exceptions import ConfigError
from .default import NAMELIST_DEFAULTS
from .._asset_list import config_to_asset_list
from ..filesystem import get_fs


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


def _get_date(config, coupler_res_date_getter):
    """Return date from configuration dictionary.  This function may read from
    the remote initial_conditions path in the given configuration dictionary.

    Args:
        config (dict): a configuration dictionary
        coupler_res_date_getter (func): a function that reads either the
            initialization_date or the current date from a coupler.res file

    Returns:
        list: date as list of ints [year, month, day, hour, min, sec]
    """
    force_date_from_namelist = config["namelist"]["coupler_nml"].get(
        "force_date_from_namelist", False
    )
    # following code replicates the logic that the fv3gfs model uses to determine the current_date
    if force_date_from_namelist:
        date = config["namelist"]["coupler_nml"].get("current_date", [0, 0, 0, 0, 0, 0])
    else:
        coupler_res_filename = _get_coupler_res_filename(config)
        if coupler_res_filename is not None:
            date = coupler_res_date_getter(coupler_res_filename)
        else:
            date = config["namelist"]["coupler_nml"].get(
                "current_date", [0, 0, 0, 0, 0, 0]
            )
    return date


def get_current_date(config):
    """Return current_date from configuration dictionary. This function may read from
    the remote initial_conditions path in the given configuration dictionary.

    Args:
        config (dict): a configuration dictionary

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    return _get_date(config, _get_current_date_from_coupler_res)


def get_diag_table_base_date(config):
    """Return base_date from configuration dictionary. This function may read from
    the remote initial_conditions path in the given configuration dictionary.

    In the event that force_date_from_namelist is specified in the config, this
    function returns the current_date or a null date if that does not exist.  If the
    date is not set to be forced from the namelist, this function first looks for the
    existence of a coupler.res file, and if it exists, returns the initialization_date
    written within it. If a coupler.res files does not exist, the current_date
    specified in the namelist or a null date is used.  To FV3GFS, a null date and
    the current date are equivalent.

    Returning the initialization_date instead of the current_date if a coupler.res
    file exists is important for obtaining reproducible restarts in segmented runs.
    Another advantage is that it harmonizes the units used to encode times in
    fotran-generated diagnostics files across segments. See more discussion in
    GH 147.

    Args:
        config (dict): a configuration dictionary

    Returns:
        list: base_date as list of ints [year, month, day, hour, min, sec]
    """
    return _get_date(config, _get_initialization_date_from_coupler_res)


def _parse_date_from_line(line, coupler_res_filename):
    """Parses a date from a line in a coupler.res file"""
    date = [int(d) for d in re.findall(r"\d+", line)]
    if len(date) != 6:
        raise ConfigError(
            f"{coupler_res_filename} does not have a valid date in the given line "
            f"(line must contain six integers)"
        )
    return date


def _read_coupler_res_dates(coupler_res_filename):
    """Read the dates contained in a coupler.res file
    
    Args:
        coupler_res_filename (str): a coupler.res filename

    Returns:
        initialization_date (list): date as list of ints [year, month, day, hour, min, sec]
        current_date (list): date as list of ints [year, month, day, hour, min, sec]
    """
    fs = get_fs(coupler_res_filename)
    with fs.open(coupler_res_filename, mode="r") as f:
        lines = f.readlines()
        initialization_date = _parse_date_from_line(lines[1], coupler_res_filename)
        current_date = _parse_date_from_line(lines[2], coupler_res_filename)
    return initialization_date, current_date


def _get_initialization_date_from_coupler_res(coupler_res_filename):
    """Return initialization_date specified in coupler.res file

    Args:
        coupler_res_filename (str): a coupler.res filename

    Returns:
        list: initialization_date as list of ints [year, month, day, hour, min, sec]
    """
    initialization_date, _ = _read_coupler_res_dates(coupler_res_filename)
    return initialization_date


def _get_current_date_from_coupler_res(coupler_res_filename):
    """Return current_date specified in coupler.res file

    Args:
        coupler_res_filename (str): a coupler.res filename

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    _, current_date = _read_coupler_res_dates(coupler_res_filename)
    return current_date


def _get_coupler_res_filename(config):
    """Return source path for coupler.res file, if it exists in config assets."""
    asset_list = config_to_asset_list(config)
    source_path = None
    for item in asset_list:
        target_path = os.path.join(item["target_location"], item["target_name"])
        if target_path == "INPUT/coupler.res":
            if "bytes" in item:
                raise NotImplementedError(
                    "Using a bytes dict to represent a coupler.res file is not "
                    "implemented yet. Use a standard asset dict for this item."
                )
            source_path = os.path.join(item["source_location"], item["source_name"])
    return source_path


def get_timestep(config):
    """Get the model timestep from a configuration dictionary.

    Args:
        config (dict): a configuration dictionary

    Returns:
        datetime.timedelta: the model timestep
    """
    return timedelta(seconds=config["namelist"]["coupler_nml"]["dt_atmos"])
