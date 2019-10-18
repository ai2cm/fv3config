import os
import appdirs
from .exceptions import ConfigError
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
inputdata_dir = os.path.join(app_data_dir, 'inputdata')

dirname = '2019-09-27-FV3GFS-docker-input-c48-LH-nml'
filename = 'fv3gfs-data-docker_2019-09-27.tar.gz'
url = f'http://storage.googleapis.com/vcm-ml-public/{dirname}/{filename}'

local_archive_filename = os.path.join(app_data_dir, filename)

forcing_directory_dict = {
    'default': os.path.join(inputdata_dir, 'forcing_base')
}

diag_table_options_dict = {
    'default': os.path.join(inputdata_dir, 'diag_table')
}


def get_resolution(config):
    npx = config['fv_core_nml']['npx']
    npy = config['fv_core_nml']['npy']
    if npx != npy:
        raise ConfigError(f'npx and npy in fv_core_nml must be equal, but are {npx} and {npy}')
    resolution = f'C{npx-1}'
    return resolution


def get_orographic_forcing_directory(config):
    resolution = get_resolution(config)
    dirname = os.path.join(inputdata_dir, f'orographic_data/{resolution}')
    if not os.path.isdir(dirname):
        valid_options = os.listdir(os.path.join(inputdata_dir, 'orographic_data'))
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
            raise NotImplemenedError(
                'Default initial conditions only available for C48, please specify an initial conditions directory'
            )
        dirname = os.path.join(inputdata_dir, 'gfs_initial_conditions')
    return dirname


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


def get_field_table_filename(config):
    if 'field_table' in config:
        filename = config.get('field_table')
        if not os.path.isfile(config['field_table']):
            raise ConfigError(f'Specified field table {filename} does not exist')
    elif config['gfs_physics_nml'].get('imp_physics', 11) != 11:
        raise NotImplemenedError(
            'Currently only have a field_table for GFS physics (gfs_physics_nml.imp_physics = 11)'
        )
    else:
        filename = os.path.join(inputdata_dir, 'field_table')
    return filename


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


def ensure_data_is_downloaded():
    if not os.path.isfile(local_archive_filename):
        download_data_archive()
    if not os.path.isdir(app_data_dir):
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


ensure_data_is_downloaded()

if __name__ == '__main__':
    pass
