import os
import tarfile
import shutil
import logging
import appdirs
from subprocess import check_call
from ._exceptions import ConfigError, DataMissingError
try:
    import wget
except ImportError:
    wget = None
    import requests

app_name = 'fv3gfs'
app_author = 'vulcan'

app_data_dir = appdirs.user_data_dir(app_name, app_author)
local_archive_dir = os.path.join(app_data_dir, 'archive')

filename = '2019-10-23-data-for-running-fv3gfs.tar.gz'
filename_root = '2019-10-23-data-for-running-fv3gfs'
url = f'http://storage.googleapis.com/vcm-ml-public/{filename}'
local_archive_filename = os.path.join(app_data_dir, filename)
gs_bucket_prefix = 'gs://'

forcing_options_dict = {
    'default': os.path.join(local_archive_dir, 'base_forcing')
}

initial_conditions_options_dict = {
    'gfs_example': os.path.join(local_archive_dir, 'initial_conditions/gfs_initial_conditions'),
    'restart_example': os.path.join(local_archive_dir, 'initial_conditions/restart_initial_conditions'),
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
    """Return the string path of the orographic forcing directory specified by a config dictionary.
    """
    resolution = get_resolution(config)
    dirname = os.path.join(local_archive_dir, f'orographic_data/{resolution}')
    if not os.path.isdir(dirname):
        valid_options = os.listdir(os.path.join(local_archive_dir, 'orographic_data'))
        raise ConfigError(f'resolution {resolution} is unsupported; valid options are {valid_options}')
    return dirname


def get_base_forcing_directory(config):
    """Return the string path of the base forcing directory specified by a config dictionary.
    """
    if 'forcing' not in config:
        raise ConfigError('config dictionary must have a \'forcing\' key')
    return resolve_option(config['forcing'], forcing_options_dict)


def get_initial_conditions_directory(config):
    """Return the string path of the initial conditions directory specified by a config dictionary.
    """
    if 'initial_conditions' not in config:
        raise ConfigError('config dictionary must have an \'initial_conditions\' key')
    return resolve_option(config['initial_conditions'], initial_conditions_options_dict)


def link_or_copy_directory(source_path, target_path):
    """Symbolically link or gsutil copy files in a source path to a target path"""
    if is_gsbucket_url(source_path):
        if gsutil_is_installed():
            check_call(['gsutil', '-m', 'cp', '-r', os.path.join(source_path, '*'), target_path])
        else:
            logging.warning(f'Optional dependency gsutil not found. Files in {source_path} will not be copied to {target_path}')
    else:
        link_directory(source_path, target_path)


def link_directory(source_path, target_path):
    """Recursively symbolic link the files in a source path into a target path.
    """
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


def check_if_data_is_downloaded():
    if not os.path.isdir(local_archive_dir):
        raise DataMissingError(
            f'Required data for running fv3gfs not available. Try python -m fv3config.download_data or ensure_data_is_downloaded()'
        )


def ensure_data_is_downloaded():
    """Check of the cached data is present, and if not, download it."""
    if not os.path.isfile(local_archive_filename):
        download_data_archive()
    if not os.path.isdir(local_archive_dir):
        extract_data()


def refresh_downloaded_data():
    """Delete the cached data (if present) and re-download it."""
    os.remove(local_archive_filename)
    shutil.rmtree(app_data_dir)
    ensure_data_is_downloaded()


def download_data_archive():
    """Download the cached data. Raises FileExistsError if data is already present."""
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
    """Extract the downloaded archive, over-writing any data already present."""
    with tarfile.open(os.path.join(app_data_dir, filename), mode='r:gz') as f:
        f.extractall(app_data_dir)
        shutil.move(os.path.join(app_data_dir, filename_root), local_archive_dir)


def is_gsbucket_url(path):
    if path.startswith(gs_bucket_prefix):
        return True
    else:
        return False


def resolve_option(option, built_in_options_dict):
    """Determine whether a configuration dictionary option is a built-in option or
    not and return path to file or directory representing option. An option is
    assumed to be built-in  if it is not an absolute path and does not begin with gs://

    Args:
        option (str): an option
        built_in_options_dict (dict): built-in options

    Returns:
        (str): a path or url

    Raises:
        ConfigError: if option is an absolute path but does not exist or if
                     option is not in default_options_dict
    """
    if os.path.isabs(option):
        if os.path.exists(option):
            return option
        else:
            raise ConfigError(
                f'The provided path {option} does not exist.'
            )
    elif is_gsbucket_url(option):
        return option
    else:
        if option in built_in_options_dict:
            return built_in_options_dict[option]
        else:
            raise ConfigError(
                f'The option {option} is not one of the built in options: {list(built_in_options_dict.keys())}'
            )


if __name__ == '__main__':
    pass
