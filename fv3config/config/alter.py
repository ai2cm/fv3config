from datetime import timedelta
import copy
from .time_constants import SECONDS_IN_DAY
from .._exceptions import ConfigError


def enable_restart(config):
    """Apply namelist settings for initializing from model restart files.

    Args:
        config (dict): a configuration dictionary

    Returns:
        dict: a configuration dictionary
    """
    if "namelist" not in config:
        raise ConfigError("config dictionary must have a 'namelist' key")
    if "fv_core_nml" not in config["namelist"]:
        raise ConfigError("config dictionary must have a 'fv_core_nml' namelist")
    restart_config = copy.deepcopy(config)
    restart_config["namelist"]["fv_core_nml"]["external_ic"] = False
    restart_config["namelist"]["fv_core_nml"]["nggps_ic"] = False
    restart_config["namelist"]["fv_core_nml"]["make_nh"] = False
    restart_config["namelist"]["fv_core_nml"]["mountain"] = True
    restart_config["namelist"]["fv_core_nml"]["warm_start"] = True
    restart_config["namelist"]["fv_core_nml"]["na_init"] = 0
    return restart_config


def set_run_duration(config: dict, duration: timedelta) -> dict:
    """Set the run duration in the configuration dictionary.

    Returns a new configuration dictionary.

    Args:
        config (dict): a configuration dictionary
        duration (timedelta): the new run duration

    Returns:
        new_config (dict): configuration dictionary with the new run duration

    Raises:
        ConfigError: if the config dictionary is invalid
    """
    if "namelist" not in config:
        raise ConfigError("config dictionary must have a 'namelist' key")
    return_config = copy.deepcopy(config)
    coupler_nml = return_config["namelist"]["coupler_nml"]
    total_seconds = duration.total_seconds()
    if total_seconds % 1 != 0:
        raise ValueError("duration must be an integer number of seconds")
    coupler_nml["months"] = 0
    coupler_nml["hours"] = 0
    coupler_nml["minutes"] = 0
    days = int(total_seconds / SECONDS_IN_DAY)
    coupler_nml["days"] = days
    coupler_nml["seconds"] = int(total_seconds - (days * SECONDS_IN_DAY))
    return return_config
