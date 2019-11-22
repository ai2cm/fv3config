import tempfile
import os
import logging
import contextlib
import subprocess
import glob
import warnings
import resource
import yaml
import gcsfs
from .._config import write_run_directory, _get_n_processes


MODULE_NAME = 'fv3config.fv3run'
STDOUT_FILENAME = 'stdout.log'
STDERR_FILENAME = 'stderr.log'
CONFIG_OUT_FILENAME = 'fv3config.yaml'
GOOGLE_PROJECT = 'VCM-ML'
DOCKER_OUTDIR = '/outdir'
DOCKER_CONFIG_LOCATION = '/fv3config.yaml'
DOCKER_RUNFILE = '/runfile.py'
DOCKER_COMMAND = ['docker', 'run']
DOCKER_KEYFILE = '/gcs_key.json'


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


def _src_is_file(src, fs):
    remote_path_list = fs.ls(src)
    if len(remote_path_list) == 0:
        raise ValueError(f'remote source {src} does not exist - is there a typo?')
    if len(remote_path_list) == 1 and remote_path_list[0].strip('gs://') == src.strip('gs://'):
        return True
    else:
        return False


def _google_cloud_copy(src, dest, fs=None):
    if fs is None:
        fs = gcsfs.GCSFileSystem(project=GOOGLE_PROJECT)
    remote_path_list = fs.ls(src)
    if _src_is_file(src, fs):
        fs.get(remote_path_list[0], dest)
    else:
        for remote_path in remote_path_list:
            basename = os.path.basename(remote_path)
            if remote_path.strip('gs://') == src.strip('gs://'):
                fs.get(remote_path, dest)
            else:  # remote path is directory
                subdir = os.path.join(dest, basename)
                os.makedirs(subdir, exist_ok=True)
                _google_cloud_copy(remote_path, subdir, fs=fs)


def _get_credentials_args(keyfile, docker_args, bind_mount_args):
    if keyfile is not None:
        bind_mount_args += ['-v', f'{os.path.abspath(keyfile)}:{DOCKER_KEYFILE}']
        docker_args += ['-e', f'GOOGLE_APPLICATION_CREDENTIALS={DOCKER_KEYFILE}']


def run(config_dict_or_location, outdir, runfile=None, dockerimage=None, keyfile=None):
    if keyfile is None:
        keyfile = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', None)
    if dockerimage is not None:
        _run_in_docker(
            config_dict_or_location, outdir, dockerimage,
            runfile=runfile, keyfile=keyfile
        )
    else:
        _run_native(config_dict_or_location, outdir, runfile=runfile)


def _is_google_cloud_path(path):
    return path[:5] == 'gs://'


def _get_runfile_args(runfile, bind_mount_args, python_args):
    if runfile is not None:
        if _is_google_cloud_path(runfile):
            python_args += ['--runfile', runfile]
        else:
            bind_mount_args += ['-v', f'{os.path.abspath(runfile)}:{DOCKER_RUNFILE}']
            python_args += ['--runfile', DOCKER_RUNFILE]


def _get_config_args(config_dict_or_location, config_tempfile, bind_mount_args):
    if isinstance(config_dict_or_location, str):
        if _is_google_cloud_path(config_dict_or_location):
            config_location = config_dict_or_location
        else:
            bind_mount_args += [
                '-v', f'{os.path.abspath(config_dict_or_location)}:{DOCKER_CONFIG_LOCATION}']
            config_location = DOCKER_CONFIG_LOCATION
    else:
        _write_config_dict(config_dict_or_location, config_tempfile.name)
        bind_mount_args += ['-v', f"{config_tempfile.name}:{DOCKER_CONFIG_LOCATION}"]
        config_location = DOCKER_CONFIG_LOCATION
    return config_location


def _get_docker_args(docker_args, bind_mount_args, outdir):
    bind_mount_args += ['-v', f"{os.path.abspath(outdir)}:{DOCKER_OUTDIR}"]
    docker_args += ['--user', f'{os.getuid()}:{os.getgid()}']


def _run_in_docker(config_dict_or_location, outdir, dockerimage, runfile=None, keyfile=None):
    with tempfile.NamedTemporaryFile(suffix='.yaml') as config_tempfile:
        bind_mount_args = []
        python_args = []
        docker_args = []
        config_location = _get_config_args(config_dict_or_location, config_tempfile, bind_mount_args)
        _get_docker_args(docker_args, bind_mount_args, outdir)
        _get_credentials_args(keyfile, docker_args, bind_mount_args)
        _get_runfile_args(runfile, bind_mount_args, python_args)
        python_command = [
            'python3', '-m', MODULE_NAME, config_location, DOCKER_OUTDIR]
        subprocess.check_call(
            DOCKER_COMMAND + bind_mount_args + docker_args + [dockerimage] + python_command + python_args)


@contextlib.contextmanager
def _temporary_directory(outdir):
    with tempfile.TemporaryDirectory() as tempdir:
        try:
            yield tempdir
        finally:
            logging.info(f'Copying output to {outdir}')
            os.makedirs(outdir, exist_ok=True)
            for source in glob.glob(os.path.join(tempdir, '*')):
                _copy(source, outdir)


def _set_stacksize_unlimited():
    try:
        resource.setrlimit(
            resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
        )
    except ValueError:
        warnings.warn(
            'could not remove stacksize limit, may run out of memory as a result'
        )


def _run_native(config_dict_or_location, outdir, runfile=None):
    _set_stacksize_unlimited()
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
        outfile.write(yaml.dump(config))


def _copy_and_load_config_dict(config_location, config_target_location):
    _copy(config_location, config_target_location)
    with open(config_target_location, 'r') as infile:
        config_dict = yaml.load(infile.read(), Loader=yaml.SafeLoader)
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
        logging.info(f'Running experiment in {dirname}')
        subprocess.check_call(
            ["mpirun", "-n", str(n_processes)] + mpi_flags + python_args,
            cwd=dirname, stdout=out_file, stderr=err_file
        )


def _get_basename_or_none(runfile):
    if runfile is None:
        return None
    else:
        return os.path.basename(runfile)
