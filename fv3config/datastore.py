import os
import appdirs
#from .exceptions import FileExistsError
try:
    import wget
except ImportError:
    wget = None
    import requests
import tarfile
import shutil
from glob import glob

class FileExistsError(Exception):
    pass

app_name = 'fv3gfs'
app_author = 'vulcan'

app_data_dir = appdirs.user_data_dir(app_name, app_author)
inputdata_dir = os.path.join(app_data_dir, 'inputdata')

dirname = '2019-09-27-FV3GFS-docker-input-c48-LH-nml'
filename = 'fv3gfs-data-docker_2019-09-27.tar.gz'
url = f'http://storage.googleapis.com/vcm-ml-public/{dirname}/{filename}'

local_archive_filename = os.path.join(app_data_dir, filename)


def get_orographic_forcing_directory():
    pass


def get_base_forcing_directory():
    pass


def data_is_downloaded():
    pass


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


def sort_files():
    """
    Re-organizes files in the newly extracted fv3gfs-data-dir to be more useful for this package.
    """
    shutil.move(os.path.join(app_data_dir, 'fv3gfs-data-docker'), inputdata_dir)
    dirname = inputdata_dir
    os.mkdir(os.path.join(dirname, 'gfs_initial_conditions'))
    gfs_filenames = glob(os.path.join(dirname, 'rundir/INPUT/gfs_*.nc')) + glob(os.path.join(dirname, 'rundir/INPUT/sfc_*.nc'))
    for filename in gfs_filenames:
        shutil.move(filename, os.path.join(dirname, 'gfs_initial_conditions', os.path.basename(filename)))
    shutil.move(os.path.join(dirname, 'rundir'), os.path.join(dirname, 'forcing_base'))
    os.rmdir(os.path.join(dirname, 'forcing_base/RESTART'))


if __name__ == '__main__':
    if not os.path.isfile(local_archive_filename):
        download_data_archive()
    shutil.rmtree(inputdata_dir)
    extract_data()
    sort_files()
