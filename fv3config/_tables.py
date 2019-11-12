import os
import re
from ._exceptions import ConfigError
from ._datastore import get_initial_conditions_directory, resolve_option


package_directory = os.path.dirname(os.path.realpath(__file__))


data_table_options_dict = {
    'default': os.path.join(package_directory, 'data/data_table/data_table_default'),
}

diag_table_options_dict = {
    'default': os.path.join(package_directory, 'data/diag_table/diag_table_default'),
    'no_output': os.path.join(package_directory, 'data/diag_table/diag_table_no_output'),
    'grid_spec': os.path.join(package_directory, 'data/diag_table/diag_table_grid_spec'),
}

field_table_options_dict = {
    'GFDLMP': os.path.join(package_directory, 'data/field_table/field_table_GFDLMP'),
    'ZhaoCarr': os.path.join(package_directory, 'data/field_table/field_table_ZhaoCarr'),
}


def get_data_table_filename(config):
    """Return filename for data_table specified in config

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: data_table filename
    """
    if 'data_table' not in config:
        raise ConfigError('config dictionary must have a \'data_table\' key')
    return resolve_option(config['data_table'], data_table_options_dict)


def get_diag_table_filename(config):
    """Return filename for diag_table specified in config

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: diag_table filename
    """
    if 'diag_table' not in config:
        raise ConfigError('config dictionary must have a \'diag_table\' key')
    return resolve_option(config['diag_table'], diag_table_options_dict)


def get_current_date_from_coupler_res(coupler_res_filename):
    """Return current_date specified in coupler.res file

    Args:
        coupler_res_filename (str): a coupler.res filename

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    with open(coupler_res_filename) as f:
        third_line = f.readlines()[2]
        current_date = [int(d) for d in re.findall(r'\d+', third_line)]
        if len(current_date) != 6:
            raise ConfigError(
                f'{coupler_res_filename} does not have a valid current model time (need six integers on third line)'
            )
    return current_date


def get_current_date_from_config(config):
    """Return current_date from configuration dictionary

    Args:
        config (dict): a configuration dictionary

    Returns:
        list: current_date as list of ints [year, month, day, hour, min, sec]
    """
    force_date_from_namelist = config['namelist']['coupler_nml'].get('force_date_from_namelist', False)
    if force_date_from_namelist:
        current_date = config['namelist']['coupler_nml'].get('current_date', [0, 0, 0, 0, 0, 0])
    else:
        coupler_res_filename = os.path.join(get_initial_conditions_directory(config), 'coupler.res')
        if os.path.exists(coupler_res_filename):
            current_date = get_current_date_from_coupler_res(coupler_res_filename)
        else:
            current_date = config['namelist']['coupler_nml'].get('current_date', [0, 0, 0, 0, 0, 0])
    return current_date


def update_diag_table_for_config(config, diag_table_filename):
    """Re-write first two lines of diag_table_filename with experiment_name
    and current_date from config dictionary.

    Args:
        config (dict): a configuration dictionary
        diag_table_filename (str): diag_table filename
    """
    if 'experiment_name' not in config:
        raise ConfigError('config dictionary must have a \'experiment_name\' key')
    temporary_diag_table_filename = f'{diag_table_filename}_temporary'
    with open(diag_table_filename) as diag_table:
        lines = diag_table.read().splitlines()
        lines[0] = config['experiment_name']
        lines[1] = ' '.join([str(x) for x in get_current_date_from_config(config)])
        with open(temporary_diag_table_filename, 'w') as temporary_diag_table:
            temporary_diag_table.write('\n'.join(lines))
    os.replace(temporary_diag_table_filename, diag_table_filename)


def get_microphysics_name_from_config(config):
    """Get name of microphysics scheme from configuration dictionary

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: name of microphysics scheme

    Raises:
        NotImplementedError: no microphysics name defined for specified
            imp_physics and ncld combination
    """
    imp_physics = config['namelist']['gfs_physics_nml'].get('imp_physics')
    ncld = config['namelist']['gfs_physics_nml'].get('ncld')
    if imp_physics == 11 and ncld == 5:
        microphysics_name = 'GFDLMP'
    elif imp_physics == 99 and ncld == 1:
        microphysics_name = 'ZhaoCarr'
    else:
        raise NotImplementedError(
            f'Microphysics choice imp_physics={imp_physics} and ncld={ncld} not one of the valid options'
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
    microphysics_name = get_microphysics_name_from_config(config)
    if microphysics_name in field_table_options_dict.keys():
        filename = field_table_options_dict[microphysics_name]
    else:
        raise NotImplementedError(
            f'Field table does not exist for {microphysics_name} microphysics'
        )
    return filename
