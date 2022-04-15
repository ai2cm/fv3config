from fv3config._exceptions import ConfigError
from .._asset_list import is_dict_or_list, ensure_is_list, asset_list_from_path
from ..filesystem import ensure_exists


def get_initial_conditions_directory(config):
    """Return the string path of the initial conditions directory
    specified by a config dictionary.
    """
    if "initial_conditions" not in config:
        raise ConfigError("config dictionary must have an 'initial_conditions' key")
    ensure_exists(config["initial_conditions"], "initial_conditions")
    return config["initial_conditions"]


def get_initial_conditions_asset_list(config):
    """Return asset_list for initial conditions. """
    if is_dict_or_list(config["initial_conditions"]):
        return ensure_is_list(config["initial_conditions"])
    else:
        source_directory = get_initial_conditions_directory(config)
        return asset_list_from_path(source_directory, target_location="INPUT")
