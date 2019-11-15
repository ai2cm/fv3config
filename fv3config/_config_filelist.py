import os
from ._datastore import (
    get_initial_conditions_directory, get_orographic_forcing_directory,
    get_base_forcing_directory, is_gsbucket_url, copy_file, link_file
)
from ._tables import (
    get_data_table_filename, get_diag_table_filename, get_field_table_filename
)


def is_dict_or_list(option):
    return isinstance(option, dict) or isinstance(option, list)


def get_orographic_forcing_filelist(config):
    source_directory = get_orographic_forcing_directory(config)
    return config_filelist_from_path(source_directory, 'INPUT', target_type='symlink')


def get_base_forcing_filelist(config):
    if is_dict_or_list(config['forcing']):
        return config['forcing']
    else:
        source_directory = get_base_forcing_directory(config)
        return config_filelist_from_path(source_directory, '/', target_type='symlink')


def get_initial_conditions_filelist(config):
    if is_dict_or_list(config['initial_conditions']):
        return config['initial_conditions']
    else:
        source_directory = get_initial_conditions_directory(config)
        return config_filelist_from_path(source_directory, 'INPUT', target_type='copy')


def get_data_table_filelist_item(config):
    data_table_filename = get_data_table_filename(config)
    location, name = os.path.split(data_table_filename)
    return generate_config_filelist_item(location, name)


def get_diag_table_filelist_item(config):
    diag_table_filename = get_diag_table_filename(config)
    location, name = os.path.split(diag_table_filename)
    return generate_config_filelist_item(location, name)


def get_field_table_filelist_item(config):
    field_table_filename = get_field_table_filename(config)
    location, name = os.path.split(field_table_filename)
    return generate_config_filelist_item(location, name)


def generate_config_filelist_item(source_location, source_name, target_location='/',
                                  target_name=None, target_type='copy'):
    if target_name is None:
        target_name = source_name
    config_filelist_item = {
        'source_location': source_location,
        'source_name': source_name,
        'target_location': target_location,
        'target_name': target_name,
        'target_type': target_type,
    }
    return config_filelist_item


def config_filelist_from_path(source_directory, target_directory='/', target_type='copy'):
    if is_gsbucket_url(source_directory):
        return config_filelist_from_gs_bucket(source_directory, target_directory)
    else:
        return config_filelist_from_local_dir(source_directory, target_directory,
                                              target_type=target_type)


def config_filelist_from_local_dir(source_directory, target_directory='/', target_type='copy'):
    """Return config_filelist from all files in source_directory with target location equal to
    target_directory. Will recurse to subdirectories if they exist."""
    config_filelist = []
    for path in os.listdir(source_directory):
        if os.path.isfile(path):
            config_filelist.append(generate_config_filelist_item(source_directory,
                                                                 os.path.basename(path),
                                                                 target_location=target_directory,
                                                                 target_type=target_type))
        elif os.path.isdir(path):
            source_subdirectory = os.path.join(source_directory, path)
            target_subdirectory = os.path.join(target_directory, path)
            config_filelist += config_filelist_from_local_dir(source_subdirectory,
                                                              target_subdirectory,
                                                              target_type=target_type)
    return config_filelist


def config_filelist_from_gs_bucket(source_directory, target_directory='/'):
    """Return config_filelist from all files in source_directory with target location equal to
    target_directory"""
    config_filelist = []
    return config_filelist


def save_filelist_item(item):
    source_path = os.path.join(item['source_location'], item['source_name'])
    target_path = os.path.join(item['target_location'], item['target_name'])
    if item['target_type'] == 'copy':
        copy_file(source_path, target_path)
    elif item['target_type'] == 'symlink':
        link_file(source_path, target_path)
