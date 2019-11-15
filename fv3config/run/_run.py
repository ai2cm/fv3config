import tempfile
import os
import logging
import contextlib
import subprocess
import yaml
import gcsfs
import glob
from .._config import write_run_directory, _get_n_processes


MODULE_NAME = 'fv3config.run'
STDOUT_FILENAME = 'stdout.log'
STDERR_FILENAME = 'stderr.log'
DOCKER_FLAGS = '-it'
CONFIG_OUT_FILENAME = 'fv3config.yaml'
GOOGLE_PROJECT = 'VCM-ML'


@contextlib.contextmanager
def _log_exceptions(localdir):
    logging.info("running experiment")
    try:
        yield
    except subprocess.CalledProcessError as e:
        logging.critical(
            "Experiment failed. Listing rundir for debugging purposes: %s",
            os.listdir(localdir)
        )
        raise e


def _copy(src, dest):
    if src[:5] == 'gs://':
        _google_cloud_copy(src, dest)
    else:
        subprocess.check_call(['cp', '-r', src, dest])


def _remote_path_is_filename(remote_path, src):
    return remote_path.strip('gs://') == src.strip('gs://')


def _google_cloud_copy(src, dest, fs=None):
    if fs is None:
        fs = gcsfs.GCSFileSystem(project=GOOGLE_PROJECT)
    remote_path_list = fs.ls(src)
    if len(remote_path_list) == 0:
        raise ValueError(f'remote source {src} does not exist - is there a typo?')
    for remote_path in remote_path_list:
        basename = os.path.basename(remote_path)
        if _remote_path_is_filename(remote_path, src):
            fs.get(remote_path, dest)
        else:  # remote path is directory
            subdir = os.path.join(dest, basename)
            os.makedirs(subdir, exist_ok=True)
            _google_cloud_copy(remote_path, subdir, fs=fs)


def _credentials_args(keyfile):
    if keyfile is not None:
        return_list = [
            '-v', f'{keyfile}:{keyfile}',
            '-e', 'GOOGLE_APPLICATION_CREDENTIALS={keyfile}'
        ]
    else:
        return_list = []
    return return_list


def run_experiment(config_dict_or_location, outdir, runfile=None, dockerimage=None, keyfile=None):
    if keyfile is None:
        keyfile = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', None)
    if dockerimage is not None:
        _run_in_docker(config_dict_or_location, outdir, dockerimage, runfile=runfile, keyfile=keyfile)
    else:
        _run_native(config_dict_or_location, outdir, runfile=runfile)


def _run_in_docker(config_dict_or_location, outdir, dockerimage, runfile=None, keyfile=None):
    with tempfile.TemporaryFile() as temp_file:
        if isinstance(config_dict_or_location, str):
            bind_mount_args = []
            config_location = config_dict_or_location
        else:
            _write_config_dict(config_dict_or_location, temp_file.name)
            bind_mount_args = ['-v', f"{temp_file.name}:{temp_file.name}"]
            bind_mount_args += ['-v', f"{outdir}:{outdir}"]
            config_location = temp_file.name
        user_args = ['--user', f'{os.getuid()}:{os.getgid()}']
        docker_command = (
            ['docker', 'run'] +
            _credentials_args(keyfile) + 
            user_args +
            bind_mount_args
        )
        if DOCKER_FLAGS:
            docker_command.append(DOCKER_FLAGS)
        docker_command.append(dockerimage)
        python_command = ['python3', '-m', MODULE_NAME]
        python_args = [config_location, outdir]
        if runfile:
            python_args += ['--runfile', runfile]
        subprocess.check_call(docker_command + python_command + python_args)


@contextlib.contextmanager
def _temporary_directory(outdir):
    with tempfile.TemporaryDirectory() as tempdir:
        try:
            yield tempdir
        finally:
            os.makedirs(outdir, exist_ok=True)
            for source in glob.glob(os.path.join(tempdir, '*')):
                _copy(source, outdir)


def _run_native(config_dict_or_location, outdir, runfile=None):
    with _temporary_directory(outdir) as localdir:
        config_out_filename = os.path.join(localdir, CONFIG_OUT_FILENAME)
        config_dict = _get_config_dict_and_write(
            config_dict_or_location, config_out_filename)
        write_run_directory(config_dict, localdir)
        if runfile is not None:
            _copy(runfile, localdir)
        with _log_exceptions(localdir):
            n_processes = _get_n_processes(config_dict)
            _run_experiment(localdir, n_processes, runfile_name=_get_basename_or_none(runfile))


def _get_config_dict_and_write(config_dict_or_location, config_out_filename):
    if isinstance(config_dict_or_location, dict):
        config_dict = config_dict_or_location
        _write_config_dict(config_dict, config_out_filename)
    else:
        config_dict = _copy_and_load_config_dict(
            config_dict_or_location, config_out_filename)
    return config_dict


def _write_config_dict(config, config_out_filename):
    with open(config_out_filename, 'w') as outfile:
        yaml.write(config, outfile)


def _copy_and_load_config_dict(config_location, config_target_location):
    _copy(config_location, config_target_location)
    with open(config_target_location, 'r') as infile:
        config_dict = yaml.load(infile)
    return config_dict


def _run_experiment(dirname, n_processes, runfile_name=None, mpi_flags=None):
    if mpi_flags is None:
        mpi_flags = []
    if runfile_name is None:
        python_args = ["python3", "-m", "mpi4py", "-m", "fv3gfs.run"]
    else:
        python_args = ["python3", "-m", "mpi4py", runfile_name]
    out_filename = os.path.join(dirname, STDOUT_FILENAME)
    err_filename = os.path.join(dirname, STDERR_FILENAME)
    with open(out_filename, 'wb') as out_file, open(err_filename, 'wb') as err_file:
        subprocess.check_call(
            ["mpirun", "-n", str(n_processes)] + mpi_flags + python_args,
            cwd=dirname, stdout=out_file, stderr=err_file
        )


def _get_basename_or_none(runfile):
    if runfile is None:
        return None
    else:
        return os.path.basename(runfile)
