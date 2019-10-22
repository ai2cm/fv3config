import os
import f90nml
from .exceptions import InvalidFileError
from .datastore import (
    get_base_forcing_directory, get_orographic_forcing_directory,
    get_initial_conditions_directory, link_directory, link_file,
    get_field_table_filename, get_diag_table_filename,
    get_data_table_filename
)


package_directory = os.path.dirname(os.path.realpath(__file__))

def get_default_config():
    return f90nml.read(os.path.join(package_directory, 'data/default.nml'))


def config_to_namelist(config, namelist_filename):
    if os.path.isfile(namelist_filename):
        os.remove(namelist_filename)
    f90nml.write(config, namelist_filename)


def config_from_namelist(namelist_filename):
    try:
        return_dict = f90nml.read(namelist_filename)
    except FileNotFoundError:
        raise InvalidFileError(f'namelist {namelist_filename} does not exist')
    return return_dict


def write_run_directory(config, target_directory):
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
    link_directory(base_forcing_dir, target_directory)
    link_directory(orographic_forcing_dir, input_directory)
    link_directory(initial_conditions_dir, input_directory)
    link_file(field_table_filename, os.path.join(target_directory, 'field_table'))
    link_file(diag_table_filename, os.path.join(target_directory, 'diag_table'))
    link_file(data_table_filename, os.path.join(target_directory, 'data_table'))
    config_to_namelist(config, os.path.join(target_directory, 'input.nml'))

