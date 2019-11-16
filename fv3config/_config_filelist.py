import os
from ._datastore import (
    get_initial_conditions_directory, get_orographic_forcing_directory,
    get_base_forcing_directory, is_gsbucket_url, copy_file, link_file
)
from ._tables import (
    get_data_table_filename, get_diag_table_filename, get_field_table_filename
)
from ._exceptions import ConfigError


def is_dict_or_list(option):
    return isinstance(option, dict) or isinstance(option, list)


def get_orographic_forcing_filelist(config):
    source_directory = get_orographic_forcing_directory(config)
    return config_filelist_from_path(source_directory, 'INPUT', copy_method='symlink')


def get_base_forcing_filelist(config):
    if is_dict_or_list(config['forcing']):
        return config['forcing']
    else:
        source_directory = get_base_forcing_directory(config)
        return config_filelist_from_path(source_directory, '', copy_method='symlink')


def get_initial_conditions_filelist(config):
    if is_dict_or_list(config['initial_conditions']):
        return config['initial_conditions']
    else:
        source_directory = get_initial_conditions_directory(config)
        return config_filelist_from_path(source_directory, 'INPUT', copy_method='copy')


def get_data_table_filelist_item(config):
    data_table_filename = get_data_table_filename(config)
    location, name = os.path.split(data_table_filename)
    return generate_config_filelist_item(location, name, target_name='data_table')


def get_diag_table_filelist_item(config):
    diag_table_filename = get_diag_table_filename(config)
    location, name = os.path.split(diag_table_filename)
    return generate_config_filelist_item(location, name, target_name='diag_table')


def get_field_table_filelist_item(config):
    field_table_filename = get_field_table_filename(config)
    location, name = os.path.split(field_table_filename)
    return generate_config_filelist_item(location, name, target_name='field_table')


def generate_config_filelist_item(source_location, source_name, target_location='',
                                  target_name=None, copy_method='copy'):
    if target_name is None:
        target_name = source_name
    config_filelist_item = {
        'source_location': source_location,
        'source_name': source_name,
        'target_location': target_location,
        'target_name': target_name,
        'copy_method': copy_method,
    }
    return config_filelist_item


def config_filelist_from_path(source_directory, target_directory='', copy_method='copy'):
    if is_gsbucket_url(source_directory):
        return config_filelist_from_gs_bucket(source_directory, target_directory)
    else:
        return config_filelist_from_local_dir(source_directory, target_directory,
                                              copy_method=copy_method)


def config_filelist_from_local_dir(source_directory, target_directory='', copy_method='copy'):
    """Return config_filelist from all files in source_directory with target location equal to
    target_directory. Will recurse to subdirectories if they exist."""
    config_filelist = []
    for base_filename in os.listdir(source_directory):
        source_item = os.path.join(source_directory, base_filename)
        if os.path.isfile(source_item):
            config_filelist.append(generate_config_filelist_item(source_directory,
                                                                 base_filename,
                                                                 target_location=target_directory,
                                                                 copy_method=copy_method))
        elif os.path.isdir(source_item):
            target_subdirectory = os.path.join(target_directory, base_filename)
            config_filelist += config_filelist_from_local_dir(source_item,
                                                              target_directory=target_subdirectory,
                                                              copy_method=copy_method)
    return config_filelist


def config_filelist_from_gs_bucket(source_directory, target_directory='/'):
    """Return config_filelist from all files in source_directory with target location equal to
    target_directory"""
    #TODO: return config_filelist given google storage bucket path


def save_filelist_item(item, target_directory):
    source_path = os.path.join(item['source_location'], item['source_name'])
    target_path = os.path.join(target_directory, item['target_location'], item['target_name'])
    if item['copy_method'] == 'copy':
        copy_file(source_path, target_path)
    elif item['copy_method'] == 'symlink':
        link_file(source_path, target_path)
    else:
        raise ConfigError(f'copy_method not defined for {source_path} filelist item')
