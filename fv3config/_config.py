import copy
import os
import f90nml
from ._exceptions import InvalidFileError, ConfigError
from ._datastore import (
    get_base_forcing_directory, get_orographic_forcing_directory,
    get_initial_conditions_directory, link_or_copy_directory,
    check_if_data_is_downloaded, copy_file
)
from ._tables import (
    get_field_table_filename, get_diag_table_filename,
    get_data_table_filename, write_diag_table
)

package_directory = os.path.dirname(os.path.realpath(__file__))

namelist_options_dict = {
    'default': os.path.join(package_directory, 'data/namelist/default.nml')
}


def get_default_config():
    """Returns a default model configuration dictionary."""
    config = {}
    config['namelist'] = f90nml.read(namelist_options_dict['default'])
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
        return_dict = f90nml.read(namelist_filename)
    except FileNotFoundError:
        raise InvalidFileError(f'namelist {namelist_filename} does not exist')
    return return_dict


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
        target_directory (str): target directory, will be created if it already exists
    """
    check_if_data_is_downloaded()
    input_directory = os.path.join(target_directory, 'INPUT')
    restart_directory = os.path.join(target_directory, 'RESTART')
    initial_conditions_dir = get_initial_conditions_directory(config)
    base_forcing_dir = get_base_forcing_directory(config)
    orographic_forcing_dir = get_orographic_forcing_directory(config)
    field_table_filename = get_field_table_filename(config)
    diag_table_filename = get_diag_table_filename(config)
    data_table_filename = get_data_table_filename(config)
    for directory in [target_directory, input_directory, restart_directory]:
        if not os.path.isdir(directory):
            os.mkdir(directory)
    link_or_copy_directory(base_forcing_dir, target_directory)
    link_or_copy_directory(orographic_forcing_dir, input_directory)
    link_or_copy_directory(initial_conditions_dir, input_directory)
    copy_file(field_table_filename, os.path.join(target_directory, 'field_table'))
    copy_file(diag_table_filename, os.path.join(target_directory, 'diag_table_temporary'))
    copy_file(data_table_filename, os.path.join(target_directory, 'data_table'))
    write_diag_table(config,
                     os.path.join(target_directory, 'diag_table_temporary'),
                     os.path.join(target_directory, 'diag_table'))
    os.remove(os.path.join(target_directory, 'diag_table_temporary'))
    config_to_namelist(config, os.path.join(target_directory, 'input.nml'))

