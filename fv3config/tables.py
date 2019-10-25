import os
import re
from .exceptions import ConfigError
from .datastore import get_initial_conditions_directory


package_directory = os.path.dirname(os.path.realpath(__file__))


data_table_options_dict = {
    'default': os.path.join(package_directory, 'data/data_table/data_table_default'),
}

diag_table_options_dict = {
    'default': os.path.join(package_directory, 'data/diag_table/diag_table_default'),
}

field_table_options_dict = {
    'GFDLMP': os.path.join(package_directory, 'data/field_table/field_table_GFDLMP'),
    'ZhaoCarr': os.path.join(package_directory, 'data/field_table/field_table_ZhaoCarr'),
}


def get_data_table_filename(config):
    option = config.get('data_table', 'default')
    if os.path.isfile(option):
        return option
    elif option not in data_table_options_dict.keys():
        raise ConfigError(
            f'Data table option {option} is not one of the valid options: {list(data_table_options_dict.keys())}'
        )
    else:
        return data_table_options_dict[option]


def get_diag_table_filename(config):
    option = config.get('diag_table', 'default')
    if os.path.isfile(option):
        return option
    elif option not in diag_table_options_dict.keys():
        raise ConfigError(
            f'Diag table option {option} is not one of the valid options: {list(diag_table_options_dict.keys())}'
        )
    else:
        return diag_table_options_dict[option]


def get_current_date_from_coupler_res(coupler_res_filename):
    with open(coupler_res_filename) as f:
        third_line = f.readlines()[2]
        current_date = [int(d) for d in re.findall(r'\d+', third_line)]
        if len(current_date) != 6:
            raise ConfigError(
                f'{coupler_res_filename} does not have a valid current model time (need six integers on third line)'
            )
    return current_date


def get_current_date_from_config(config):
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


def write_diag_table(config, source_diag_table_filename, target_diag_table_filename):
    with open(source_diag_table_filename) as source_diag_table:
        lines = source_diag_table.read().splitlines()
        lines[0] = config.get('experiment_name', 'default_experiment')
        lines[1] = ' '.join([str(x) for x in get_current_date_from_config(config)])
        with open(target_diag_table_filename, 'w') as target_diag_table:
            target_diag_table.write('\n'.join(lines))


def get_microphysics_name_from_config(config):
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
    microphysics_name = get_microphysics_name_from_config(config)
    if microphysics_name in field_table_options_dict.keys():
        filename = field_table_options_dict[microphysics_name]
    else:
        raise NotImplementedError(
            f'Field table does not exist for {microphysics_name} microphysics'
        )
    return filename
