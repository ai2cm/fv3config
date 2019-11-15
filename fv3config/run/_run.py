import tempfile
import os
import logging
import contextlib
import subprocess
import yaml
from .._config import write_run_directory

MODULE_NAME = 'fv3config.run'
STDOUT_FILENAME = 'stdout.log'
STDERR_FILENAME = 'stderr.log'
DOCKER_FLAGS = '-it'
CONFIG_OUT_FILENAME = 'fv3config.yaml'


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


def gsutil_copy(src, dest):
    try:
        subprocess.check_call(['gsutil', '-m', 'cp', '-r', src, dest])
    except subprocess.CalledProcessError as e:
        auth_info = subprocess.check_output(['gcloud', 'auth', 'list'])
        logging.error("gsutil copy failed. authentication info: %s", auth_info)
        raise e


def run_experiment(config_dict_or_location, outdir, runfile=None, dockerimage=None):
    if dockerimage is not None:
        _run_in_docker(config_dict_or_location, outdir, dockerimage, runfile=runfile)
    else:
        _run_native(config_dict_or_location, outdir, runfile=runfile)


def _run_in_docker(config_dict_or_location, outdir, dockerimage, runfile=None):
    with tempfile.TemporaryFile() as temp_file:
        if isinstance(config_dict_or_location, str):
            bind_mount_args = []
            config_location = config_dict_or_location
        else:
            _write_config_dict(config_dict_or_location, temp_file.name)
            bind_mount_args = ['-v', f"{temp_file.name}:{temp_file.name}"]
            config_location = temp_file.name
        docker_command = ['docker', 'run'] + bind_mount_args
        if DOCKER_FLAGS:
            docker_command.append(DOCKER_FLAGS)
        docker_command.append(dockerimage)
        python_command = ['python3', '-m', MODULE_NAME]
        python_args = [config_location, outdir]
        if runfile:
            python_args += ['--runfile', runfile]
        subprocess.check_call(docker_command + python_command + python_args)


def _run_native(config_dict_or_location, outdir, runfile=None):
    with tempfile.TemporaryDirectory() as localdir:
        config_out_filename = os.path.join(localdir, CONFIG_OUT_FILENAME)
        config_dict = _get_config_dict_and_write(
            config_dict_or_location, config_out_filename)
        write_run_directory(config_dict, localdir)
        if runfile is not None:
            gsutil_copy(runfile, localdir)
        with _log_exceptions(localdir):
            _run_experiment(localdir, _get_basename_or_none(runfile))
        gsutil_copy(os.path.join(localdir, '*'), outdir)


def _get_config_dict_and_write(config_dict_or_location, config_out_filename):
    if isinstance(config_dict_or_location, dict):
        config_dict = config_dict_or_location
        _write_config_dict(config_dict, config_out_filename)
    else:
        config_dict = _copy_and_load_config_dict(
            config_dict_or_location, config_out_filename)


def _write_config_dict(config, config_out_filename):
    with open(config_out_filename, 'w') as outfile:
        yaml.write(config, outfile)


def _copy_and_load_config_dict(config_location, config_target_location):
    gsutil_copy(config_location, config_target_location)
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
