import copy
from .._exceptions import ConfigError


def enable_restart(config):
    """Apply namelist settings for initializing from model restart files.

    Args:
        config (dict): a configuration dictionary

    Returns:
        dict: a configuration dictionary
    """
    if 'namelist' not in config:
        raise ConfigError('config dictionary must have a \'namelist\' key')
    if 'fv_core_nml' not in config['namelist']:
        raise ConfigError('config dictionary must have a \'fv_core_nml\' namelist')
    restart_config = copy.deepcopy(config)
    restart_config['namelist']['fv_core_nml']['external_ic'] = False
    restart_config['namelist']['fv_core_nml']['nggps_ic'] = False
    restart_config['namelist']['fv_core_nml']['make_nh'] = False
    restart_config['namelist']['fv_core_nml']['mountain'] = True
    restart_config['namelist']['fv_core_nml']['warm_start'] = True
    restart_config['namelist']['fv_core_nml']['na_init'] = 0
    return restart_config
