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


def get_orographic_forcing_asset_list(config):
    source_directory = get_orographic_forcing_directory(config)
    return asset_list_from_path(source_directory, 'INPUT', copy_method='symlink')


def get_base_forcing_asset_list(config):
    if is_dict_or_list(config['forcing']):
        return config['forcing']
    else:
        source_directory = get_base_forcing_directory(config)
        return asset_list_from_path(source_directory, '', copy_method='symlink')


def get_initial_conditions_asset_list(config):
    if is_dict_or_list(config['initial_conditions']):
        return config['initial_conditions']
    else:
        source_directory = get_initial_conditions_directory(config)
        return asset_list_from_path(source_directory, 'INPUT', copy_method='copy')


def get_data_table_asset(config):
    data_table_filename = get_data_table_filename(config)
    location, name = os.path.split(data_table_filename)
    return generate_config_asset(location, name, target_name='data_table')


def get_diag_table_asset(config):
    diag_table_filename = get_diag_table_filename(config)
    location, name = os.path.split(diag_table_filename)
    return generate_config_asset(location, name, target_name='diag_table')


def get_field_table_asset(config):
    field_table_filename = get_field_table_filename(config)
    location, name = os.path.split(field_table_filename)
    return generate_config_asset(location, name, target_name='field_table')


def generate_config_asset(source_location, source_name, target_location='',
                                  target_name=None, copy_method='copy'):
    if target_name is None:
        target_name = source_name
    config_asset = {
        'source_location': source_location,
        'source_name': source_name,
        'target_location': target_location,
        'target_name': target_name,
        'copy_method': copy_method,
    }
    return config_asset


def asset_list_from_path(source_directory, target_directory='', copy_method='copy'):
    if is_gsbucket_url(source_directory):
        return asset_list_from_gs_bucket(source_directory, target_directory)
    else:
        return asset_list_from_local_dir(source_directory, target_directory,
                                         copy_method=copy_method)


def asset_list_from_local_dir(source_directory, target_directory='', copy_method='copy'):
    """Return asset_list from all files in source_directory with target location equal to
    target_directory. Will recurse to subdirectories if they exist."""
    asset_list = []
    for base_filename in os.listdir(source_directory):
        source_item = os.path.join(source_directory, base_filename)
        if os.path.isfile(source_item):
            asset_list.append(generate_config_asset(source_directory,
                                                    base_filename,
                                                    target_location=target_directory,
                                                    copy_method=copy_method))
        elif os.path.isdir(source_item):
            target_subdirectory = os.path.join(target_directory, base_filename)
            asset_list += asset_list_from_local_dir(source_item,
                                                    target_directory=target_subdirectory,
                                                    copy_method=copy_method)
    return asset_list


def asset_list_from_gs_bucket(source_directory, target_directory='/'):
    """Return asset_list from all files in source_directory with target location equal to
    target_directory"""
    #TODO: return asset_list given google storage bucket path


def write_asset(asset, target_directory):
    source_path = os.path.join(asset['source_location'], asset['source_name'])
    target_path = os.path.join(target_directory, asset['target_location'], asset['target_name'])
    if not os.path.exists(os.path.dirname(target_path)):
        os.makedirs(os.path.dirname(target_path))
    if asset['copy_method'] == 'copy':
        copy_file(source_path, target_path)
    elif asset['copy_method'] == 'symlink':
        link_file(source_path, target_path)
    else:
        raise ConfigError(f'copy_method not defined for {source_path} asset')


def write_asset_list(asset_list, target_directory):
    for asset in asset_list:
        write_asset(asset, target_directory)


def config_to_asset_list(config):
    asset_list = get_initial_conditions_asset_list(config)
    asset_list += get_base_forcing_asset_list(config)
    asset_list += get_orographic_forcing_asset_list(config)
    asset_list.append(get_field_table_asset(config))
    asset_list.append(get_diag_table_asset(config))
    asset_list.append(get_data_table_asset(config))
    if 'patch_files' in config:
        if isinstance(config['patch_files'], dict):
            asset_list.append(config['patch_files'])
        elif isinstance(config['patch_files'], list):
            asset_list += config['patch_files']
    return asset_list
