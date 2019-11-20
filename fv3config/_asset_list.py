import logging
import os
import shutil
from subprocess import check_call
from ._datastore import (
    get_initial_conditions_directory, get_orographic_forcing_directory,
    get_base_forcing_directory, is_gsbucket_url
)
from ._tables import (
    get_data_table_filename, get_diag_table_filename, get_field_table_filename
)
from ._exceptions import ConfigError


def is_dict_or_list(option):
    return isinstance(option, dict) or isinstance(option, list)


def ensure_is_list(asset):
    """If argument is a dict, return length 1 list containing dict"""
    if isinstance(asset, dict):
        return [asset]
    elif isinstance(asset, list):
        return asset
    else:
        raise ConfigError('Asset must be a dict or list of dicts')


def get_orographic_forcing_asset_list(config):
    """Return asset_list for orographic forcing"""
    source_directory = get_orographic_forcing_directory(config)
    return asset_list_from_path(source_directory, 'INPUT', copy_method='link')


def get_base_forcing_asset_list(config):
    """Return asset_list for base forcing"""
    if is_dict_or_list(config['forcing']):
        return ensure_is_list(config['forcing'])
    else:
        source_directory = get_base_forcing_directory(config)
        return asset_list_from_path(source_directory, '', copy_method='link')


def get_initial_conditions_asset_list(config):
    """Return asset_list for initial conditions. """
    if is_dict_or_list(config['initial_conditions']):
        return ensure_is_list(config['initial_conditions'])
    else:
        source_directory = get_initial_conditions_directory(config)
        return asset_list_from_path(source_directory, 'INPUT', copy_method='copy')


def get_data_table_asset(config):
    """Return asset for data_table"""
    data_table_filename = get_data_table_filename(config)
    location, name = os.path.split(data_table_filename)
    return generate_asset(location, name, target_name='data_table')


def get_diag_table_asset(config):
    """Return asset for diag_table"""
    diag_table_filename = get_diag_table_filename(config)
    location, name = os.path.split(diag_table_filename)
    return generate_asset(location, name, target_name='diag_table')


def get_field_table_asset(config):
    """Return asset for field_table"""
    field_table_filename = get_field_table_filename(config)
    location, name = os.path.split(field_table_filename)
    return generate_asset(location, name, target_name='field_table')


def generate_asset(source_location, source_name, target_location='',
                   target_name=None, copy_method='copy'):
    """Helper function to generate asset for a particular file

    Args:
        source_location (str): path to directory containing source file
        source_name (str): filename of source file
        target_location (str, optional): sub-directory to which file will
            be written, relative to run directory root. Defaults to empty
            string (i.e. root of run directory).
        target_name (str, optional): filename to which file will be written.
            Defaults to None, in which case source_name is used.
        copy_method (str, optional): flag to determine whether file is
            copied ('copy') or hard-linked ('link'). Defaults to 'copy'.
    """
    if target_name is None:
        target_name = source_name
    asset = {
        'source_location': source_location,
        'source_name': source_name,
        'target_location': target_location,
        'target_name': target_name,
        'copy_method': copy_method,
    }
    return asset


def asset_list_from_path(source_directory, target_directory='', copy_method='copy'):
    """Return an asset_list given either a local path or remote google storage url"""
    if is_gsbucket_url(source_directory):
        return asset_list_from_gs_bucket(source_directory, target_directory)
    else:
        return asset_list_from_local_dir(source_directory, target_directory,
                                         copy_method=copy_method)


def asset_list_from_local_dir(source_directory, target_directory='', copy_method='copy'):
    """Return asset_list from all files in source_directory (which is assumed to be
    local) with target location equal to target_directory. Will recurse to
    subdirectories if they exist.
    """
    asset_list = []
    for root, dirs, files in os.walk(source_directory):
        if root == source_directory:
            target_location = target_directory
        else:
            target_location = os.path.join(target_directory, os.path.basename(root))
        for file in files:
            asset_list.append(generate_asset(os.path.join(source_directory, root),
                                             file,
                                             target_location=target_location,
                                             copy_method=copy_method))

    return asset_list


def asset_list_from_gs_bucket(source_directory, target_directory='/'):
    """Return asset_list from all files in source_directory (which is assumed to be
    a google cloud storage url) with target location equal to target_directory"""
    #TODO: return asset_list given google storage bucket path


def write_asset(asset, target_directory):
    """Write file represented by asset to target_directory

    Args:
        asset (dict): an asset dict
        target_directory (str): path to a directory in which all files will be written
    """
    check_asset_valid(asset)
    source_path = os.path.join(asset['source_location'], asset['source_name'])
    target_path = os.path.join(target_directory, asset['target_location'], asset['target_name'])
    copy_method = asset['copy_method']
    if not os.path.exists(os.path.dirname(target_path)):
        os.makedirs(os.path.dirname(target_path))
    if copy_method == 'copy':
        copy_file(source_path, target_path)
    elif copy_method == 'link':
        link_file(source_path, target_path)
    else:
        raise ConfigError(
            f'Behavior of copy_method {copy_method} not defined for {source_path} asset'
        )


def write_asset_list(asset_list, target_directory):
    """Loop over list of assets and write them all"""
    for asset in asset_list:
        write_asset(asset, target_directory)


def check_asset_valid(asset):
    """Check asset has all of its required keys"""
    required_asset_properties = ['source_location', 'source_name', 'target_location',
                                 'target_name', 'copy_method']
    for required_asset_property in required_asset_properties:
        if required_asset_property not in asset:
            raise ConfigError(f'Assets must have a {required_asset_property}')


def config_to_asset_list(config):
    """Convert a configuration dictionary to an asset list. The asset list
    will contain all files for the run directory except the namelist."""
    asset_list = get_initial_conditions_asset_list(config)
    asset_list += get_base_forcing_asset_list(config)
    asset_list += get_orographic_forcing_asset_list(config)
    asset_list.append(get_field_table_asset(config))
    asset_list.append(get_diag_table_asset(config))
    asset_list.append(get_data_table_asset(config))
    if 'patch_files' in config:
        if is_dict_or_list(config['patch_files']):
            asset_list += ensure_is_list(config['patch_files'])
        else:
            raise ConfigError('patch_files item in config dictionary must be a dict or list')
    return asset_list


def link_file(source_item, target_item):
    if os.path.exists(target_item):
        os.remove(target_item)
    os.link(source_item, target_item)


def copy_file(source_path, target_path):
    if is_gsbucket_url(source_path):
        if gsutil_is_installed():
            check_call(['gsutil', 'cp', source_path, target_path])
        else:
            logging.warning(f'Optional dependency gsutil not found. File {source_path} will not be copied to {target_path}')
    else:
        shutil.copy(source_path, target_path)


def gsutil_is_installed():
    if shutil.which('gsutil') is None:
        return False
    else:
        return True
