import os
import re
from datetime import timedelta
import fsspec
from .._exceptions import ConfigError
from .default import NAMELIST_DEFAULTS
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


def get_current_date(config):
    """Return current_date from configuration dictionary. This function may read from
    the  remote initial_conditions path in the given configuration dictionary.

    Args:
        config (dict): a configuration dictionary

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
        coupler_res_filename = os.path.join(config["initial_conditions"], "coupler.res")
        if get_fs(coupler_res_filename).exists(coupler_res_filename):
            current_date = _get_current_date_from_coupler_res(coupler_res_filename)
        else:
            current_date = config["namelist"]["coupler_nml"].get(
                "current_date", [0, 0, 0, 0, 0, 0]
            )
    return current_date


def _get_current_date_from_coupler_res(coupler_res_filename):
    """Return current_date specified in coupler.res file

    Args:
        coupler_res_filename (str): a coupler.res filename

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    with fsspec.open(coupler_res_filename, mode="r") as f:
        third_line = f.readlines()[2]
        current_date = [int(d) for d in re.findall(r"\d+", third_line)]
        if len(current_date) != 6:
            raise ConfigError(
                f"{coupler_res_filename} does not have a valid current model time (need six integers on third line)"
            )
    return current_date


def get_resolution(config):
    """Get the model resolution based on a configuration dictionary.

    Args:
        config (dict): a configuration dictionary

    Returns:
        resolution (str): a model resolution (e.g. 'C48' or 'C96')

    Raises:
        ConfigError: if the number of processors in x and y on a tile are unequal
    """
    npx = config["namelist"]["fv_core_nml"]["npx"]
    npy = config["namelist"]["fv_core_nml"]["npy"]
    if npx != npy:
        raise ConfigError(
            f"npx and npy in fv_core_nml must be equal, but are {npx} and {npy}"
        )
    resolution = f"C{npx-1}"
    return resolution


def get_timestep(config):
    """Get the model timestep from a configuration dictionary.

    Args:
        config (dict): a configuration dictionary

    Returns:
        datetime.timedelta: the model timestep
    """
    return timedelta(seconds=config["namelist"]["coupler_nml"]["dt_atmos"])
