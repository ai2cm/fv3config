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


def get_time_metadata(config):
    """Return an initialization date and current date from a configuration
    dictionary.

    This function may read from the remote initial_conditions path given in
    the configuration dicitionary.

    Args:
        config(dict): a configuration dictionary

    Returns:
        initialization_date (list): date as list of ints [year, month, day, hour, min, sec]
        current_date (list): date as list of ints [year, month, day, hour, min, sec]
    """
    coupler_nml = config["namelist"]["coupler_nml"]
    force_date_from_namelist = coupler_nml.get("force_date_from_namelist", False)

    # following code replicates the logic that the fv3gfs model uses to determine the current_date
    if force_date_from_namelist:
        current_date = coupler_nml.get("current_date", [0, 0, 0, 0, 0, 0])
        time_metadata = (current_date, current_date)
    else:
        coupler_res_filename = _get_coupler_res_filename(config)
        if coupler_res_filename is not None:
            time_metadata = _read_time_metadata_from_coupler_res(coupler_res_filename)
        else:
            current_date = coupler_nml.get("current_date", [0, 0, 0, 0, 0, 0])
            time_metadata = (current_date, current_date)
    return time_metadata


def _parse_date_from_line(line, coupler_res_filename):
    """Parses a date from a line in a coupler.res file"""
    date = [int(d) for d in re.findall(r"\d+", line)]
    if len(date) != 6:
        raise ConfigError(
            f"{coupler_res_filename} does not have a valid date in the given line "
            f"(line must contain six integers)"
        )
    return date


def _read_time_metadata_from_coupler_res(coupler_res_filename):
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
