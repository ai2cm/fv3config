import os
from .exceptions import ConfigError


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
