import copy
import os
import f90nml
import yaml
from ._exceptions import InvalidFileError, ConfigError
from ._datastore import check_if_data_is_downloaded
from ._tables import update_diag_table_for_config, get_current_date_from_config
from ._asset_list import config_to_asset_list, write_assets_to_directory

package_directory = os.path.dirname(os.path.realpath(__file__))

namelist_options_dict = {
    'default': os.path.join(package_directory, 'data/namelist/default.nml')
}

_NAMELIST_DEFAULTS = {
    'ntiles': 6,
    'layout': (1, 1),
}


def _get_n_processes(config_dict):
    n_tiles = config_dict['namelist']['fv_core_nml'].get('ntiles', _NAMELIST_DEFAULTS['ntiles'])
    layout = config_dict['namelist']['fv_core_nml'].get('layout', _NAMELIST_DEFAULTS['layout'])
    processors_per_tile = layout[0] * layout[1]
    return n_tiles * processors_per_tile


def _write_config_dict(config, config_out_filename):
    with open(config_out_filename, 'w') as outfile:
        outfile.write(yaml.dump(config))


def get_default_config():
    """Returns a default model configuration dictionary."""
    config = {}
    config['namelist'] = config_from_namelist(namelist_options_dict['default'])
    config['diag_table'] = 'default'
    config['data_table'] = 'default'
    config['forcing'] = 'default'
    config['initial_conditions'] = 'gfs_example'
    config['experiment_name'] = 'default_experiment'

    return config


def config_to_namelist(config, namelist_filename):
    """Write a configuration dictionary to a namelist file.

    Args:
        config (dict): a configuration dictionary
        namelist_filename (str): filename to write, will be overwritten if present
    """
    if os.path.isfile(namelist_filename):
        os.remove(namelist_filename)
    f90nml.write(config['namelist'], namelist_filename)


def config_from_namelist(namelist_filename):
    """Read a configuration dictionary from a namelist file.

    Only reads the namelist configuration.

    Args:
        namelist_filename (str): a namelist filename

    Returns:
        return_dict (dict): a configuration dictionary

    Raises:
        InvalidFileError: if the specified filename does not exist
    """
    try:
        return_dict = _to_nested_dict(f90nml.read(namelist_filename).items())
    except FileNotFoundError:
        raise InvalidFileError(f'namelist {namelist_filename} does not exist')
    return return_dict


def _to_nested_dict(source):
    return_value = dict(source)
    for name, value in return_value.items():
        if isinstance(value, f90nml.Namelist):
            return_value[name] = _to_nested_dict(value)
    return return_value


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


def write_run_directory(config, target_directory):
    """Write a run directory based on a configuration dictionary.

    Args:
        config (dict): a configuration dictionary
        target_directory (str): target directory, will be created if it does not exist
    """
    check_if_data_is_downloaded()
    write_assets_to_directory(config, target_directory)
    current_date = get_current_date_from_config(config, os.path.join(target_directory, 'INPUT'))
    update_diag_table_for_config(config, current_date, os.path.join(target_directory, 'diag_table'))
    config_to_namelist(config, os.path.join(target_directory, 'input.nml'))

