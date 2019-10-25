import os
import appdirs
import logging
from .exceptions import ConfigError, NotImplementedError, DataMissingError
try:
    import wget
except ImportError:
    wget = None
    import requests
import tarfile
import shutil
from glob import glob

app_name = 'fv3gfs'
app_author = 'vulcan'

app_data_dir = appdirs.user_data_dir(app_name, app_author)
local_archive_dir = os.path.join(app_data_dir, 'archive')

filename = '2019-10-23-data-for-running-fv3gfs.tar.gz'
filename_root = '2019-10-23-data-for-running-fv3gfs'
url = f'http://storage.googleapis.com/vcm-ml-public/{filename}'
local_archive_filename = os.path.join(app_data_dir, filename)

forcing_directory_dict = {
    'default': os.path.join(local_archive_dir, 'base_forcing')
}


def get_resolution(config):
    """Get the model resolution based on a configuration dictionary.

    Args:
        config (dict): a configuration dictionary
    
    Returns:
        resolution (str): a model resolution (e.g. 'C48' or 'C96')

    Raises:
        ConfigError: if the number of processors in x and y on a tile are unequal
    """
    npx = config['namelist']['fv_core_nml']['npx']
    npy = config['namelist']['fv_core_nml']['npy']
    if npx != npy:
        raise ConfigError(f'npx and npy in fv_core_nml must be equal, but are {npx} and {npy}')
    resolution = f'C{npx-1}'
    return resolution


def get_orographic_forcing_directory(config):
    resolution = get_resolution(config)
    dirname = os.path.join(local_archive_dir, f'orographic_data/{resolution}')
    if not os.path.isdir(dirname):
        valid_options = os.listdir(os.path.join(local_archive_dir, 'orographic_data'))
        raise ConfigError(f'resolution {resolution} is unsupported; valid options are {valid_options}')
    return dirname


def get_base_forcing_directory(config):
    forcing_option = config.get('forcing', 'default')
    if os.path.isdir(forcing_option):
        return forcing_option
    elif forcing_option not in forcing_directory_dict.keys():
        raise ConfigError(
            f'Forcing option {forcing_option} is not one of the valid options: {list(forcing_directory_dict.keys())}'
        )
    else:
        return forcing_directory_dict[forcing_option]


def get_initial_conditions_directory(config):
    if 'initial_conditions' in config:
        dirname = config['initial_conditions']
        if not os.path.isdir(dirname):
            raise ConfigError(f'Specified initial conditions directory {dirname} does not exist')
    else:
        resolution = get_resolution(config)
        if resolution != 'C48':
            raise NotImplementedError(
                'Default initial conditions only available for C48, please specify an initial conditions directory'
            )
        dirname = os.path.join(local_archive_dir, 'gfs_initial_conditions')
    return dirname


def link_directory(source_path, target_path):
    for base_filename in os.listdir(source_path):
        source_item = os.path.join(source_path, base_filename)
        target_item = os.path.join(target_path, base_filename)
        if os.path.isfile(source_item):
            if os.path.exists(target_item):
                os.remove(target_item)
            os.symlink(source_item, target_item)
        elif os.path.isdir(source_item):
            if not os.path.isdir(target_item):
                os.mkdir(target_item)
            link_directory(source_item, target_item)


def link_file(source_path, target_path):
    os.symlink(source_path, target_path)


def copy_file(source_path, target_path):
    shutil.copy(source_path, target_path)


def check_if_data_is_downloaded():
    if not os.path.isdir(local_archive_dir):
        raise DataMissingError(f'Required data for running fv3gfs not available. Try python -m fv3config.download_data')


def ensure_data_is_downloaded():
    if not os.path.isfile(local_archive_filename):
        download_data_archive()
    if not os.path.isdir(local_archive_dir):
        extract_data()


def refresh_downloaded_data():
    os.remove(local_archive_filename)
    shutil.rmtree(app_data_dir)
    ensure_data_is_downloaded()


def download_data_archive():
    if os.path.isfile(local_archive_filename):
        raise FileExistsError(f'Archive already exists at {local_archive_filename}')
    if not os.path.isdir(app_data_dir):
        os.makedirs(app_data_dir, exist_ok=True)
    logging.info(f'Downloading required data for running fv3gfs to {app_data_dir}')
    if wget is not None:
        wget.download(url, out=local_archive_filename)
    else:
        r = requests.get(url)
        with open(local_archive_filename, 'wb') as f:
            f.write(r.content)


def extract_data():
    if not os.path.isdir(app_data_dir):
        os.mkdir(app_data_dir)
    with tarfile.open(os.path.join(app_data_dir, filename), mode='r:gz') as f:
        f.extractall(app_data_dir)
        shutil.move(os.path.join(app_data_dir, filename_root), local_archive_dir)


if __name__ == '__main__':
    pass
