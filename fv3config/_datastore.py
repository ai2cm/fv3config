import os
import tarfile
import shutil
import logging
import tempfile
from subprocess import check_call
import requests
import appdirs
from ._exceptions import ConfigError, DataMissingError

if 'FV3CONFIG_CACHE_DIR' in os.environ:
    LOCAL_ARCHIVE_DIR = os.environ['FV3CONFIG_CACHE_DIR']
else:
    LOCAL_ARCHIVE_DIR = os.path.join(
        appdirs.user_data_dir('fv3gfs', 'vulcan'),
        'archive'
    )


ARCHIVE_FILENAME = '2019-10-23-data-for-running-fv3gfs.tar.gz'
ARCHIVE_FILENAME_ROOT = '2019-10-23-data-for-running-fv3gfs'
ARCHIVE_URL = f'http://storage.googleapis.com/vcm-ml-public/{ARCHIVE_FILENAME}'
GS_BUCKET_PREFIX = 'gs://'

FORCING_OPTIONS_DICT = {
    'default': 'base_forcing',
}

INITIAL_CONDITIONS_OPTIONS_DICT = {
    'gfs_example': 'initial_conditions/gfs_initial_conditions',
    'restart_example': 'initial_conditions/restart_initial_conditions',
}


def set_cache_dir(dirname):
    global LOCAL_ARCHIVE_DIR
    LOCAL_ARCHIVE_DIR = dirname


def get_cache_dir():
    return LOCAL_ARCHIVE_DIR


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
    dirname = os.path.join(LOCAL_ARCHIVE_DIR, f'orographic_data/{resolution}')
    if not os.path.isdir(dirname):
        valid_options = os.listdir(os.path.join(get_cache_dir(), 'orographic_data'))
        raise ConfigError(f'resolution {resolution} is unsupported; valid options are {valid_options}')
    return dirname


def get_base_forcing_directory(config):
    """Return the string path of the base forcing directory specified by a config dictionary.
    """
    if 'forcing' not in config:
        raise ConfigError('config dictionary must have a \'forcing\' key')
    return resolve_option(config['forcing'], FORCING_OPTIONS_DICT)


def get_initial_conditions_directory(config):
    """Return the string path of the initial conditions directory specified by a config dictionary.
    """
    if 'initial_conditions' not in config:
        raise ConfigError('config dictionary must have an \'initial_conditions\' key')
    return resolve_option(config['initial_conditions'], INITIAL_CONDITIONS_OPTIONS_DICT)


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
    if not os.path.isdir(get_cache_dir()) or len(os.listdir(get_cache_dir())) == 0:
        raise DataMissingError(
            f'Required data for running fv3gfs not available. Try python -m fv3config.download_data or ensure_data_is_downloaded()'
        )


def ensure_data_is_downloaded():
    """Check of the cached data is present, and if not, download it."""
    os.makedirs(get_cache_dir(), exist_ok=True)
    if len(os.listdir(get_cache_dir())) == 0:
        with tempfile.NamedTemporaryFile(mode='wb') as archive_file:
            download_data_archive(archive_file)
            archive_file.flush()
            extract_data(archive_file.name)


def refresh_downloaded_data():
    """Delete the cached data (if present) and re-download it."""
    shutil.rmtree(get_cache_dir())
    ensure_data_is_downloaded()


def download_data_archive(target_file):
    """Download the cached data."""
    logging.info('Downloading required data for running fv3gfs to temporary file')
    r = requests.get(ARCHIVE_URL)
    target_file.write(r.content)


def extract_data(archive_filename):
    """Extract the downloaded archive, over-writing any data already present."""
    logging.info('Extracting required data for running fv3gfs to %s', get_cache_dir())
    with tarfile.open(archive_filename, mode='r:gz') as f:
        with tempfile.TemporaryDirectory() as tempdir:
            f.extractall(tempdir)
            for name in os.listdir(os.path.join(tempdir, ARCHIVE_FILENAME_ROOT)):
                shutil.move(
                    os.path.join(tempdir, ARCHIVE_FILENAME_ROOT, name),
                    get_cache_dir()
                )


def is_gsbucket_url(path):
    return path.startswith(GS_BUCKET_PREFIX)


def resolve_option(option, built_in_options_dict):
    """Determine whether a configuration dictionary option is a built-in option or
    not and return path to file or directory representing option. An option is
    assumed to be built-in if it is not an absolute path and does not begin with gs://

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
            return os.path.join(get_cache_dir(), built_in_options_dict[option])
        else:
            raise ConfigError(
                f'The provided option {option} is not one of the built in options: '
                f'{list(built_in_options_dict.keys())}. Paths to local files or directories must be absolute.'
            )
