import logging
import contextlib
import resource
import subprocess
import os
import tempfile
import warnings
import yaml
from .._config import write_run_directory, _get_n_processes, _write_config_dict
from ._gcloud import _copy_directory, _copy_file

STDOUT_FILENAME = 'stdout.log'
STDERR_FILENAME = 'stderr.log'
CONFIG_OUT_FILENAME = 'fv3config.yaml'


def _run_native(config_dict_or_location, outdir, runfile=None):
    _set_stacksize_unlimited()
    with _temporary_directory(outdir) as localdir:
        config_out_filename = os.path.join(localdir, CONFIG_OUT_FILENAME)
        # we need to write the dict to the run directory for archival and also load
        # the dict, it ends up being convenient to do both at once
        config_dict = _get_config_dict_and_write(
            config_dict_or_location, config_out_filename)
        write_run_directory(config_dict, localdir)
        if runfile is not None:
            _copy_file(runfile, os.path.join(localdir, os.path.basename(runfile)))
        with _log_exceptions(localdir):
            n_processes = _get_n_processes(config_dict)
            _run_experiment(
                localdir, n_processes, runfile_name=_get_basename_or_none(runfile))


def _set_stacksize_unlimited():
    try:
        resource.setrlimit(
            resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
        )
    except ValueError:
        warnings.warn(
            'could not remove stacksize limit, may run out of memory as a result'
        )


@contextlib.contextmanager
def _temporary_directory(outdir):
    with tempfile.TemporaryDirectory() as tempdir:
        try:
            yield tempdir
        finally:
            logging.info('Copying output to %s', outdir)
            os.makedirs(outdir, exist_ok=True)
            _copy_directory(tempdir, outdir)


@contextlib.contextmanager
def _log_exceptions(localdir):
    logging.info("running experiment")
    try:
        yield
    except subprocess.CalledProcessError as e:
        logging.critical(
            "Experiment failed. "
            "Check %s and %s for logs.",
            STDOUT_FILENAME, STDERR_FILENAME
        )
        raise e


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
        logging.info('Running experiment in %s', dirname)
        subprocess.check_call(
            ["mpirun", "-n", str(n_processes)] + mpi_flags + python_args,
            cwd=dirname, stdout=out_file, stderr=err_file
        )


def _get_basename_or_none(runfile):
    if runfile is None:
        return None
    else:
        return os.path.basename(runfile)


def _get_config_dict_and_write(config_dict_or_location, config_out_filename):
    if isinstance(config_dict_or_location, dict):
        config_dict = config_dict_or_location
        _write_config_dict(config_dict, config_out_filename)
    else:
        config_dict = _copy_and_load_config_dict(
            config_dict_or_location, config_out_filename)
    return config_dict


def _copy_and_load_config_dict(config_location, config_target_location):
    _copy_file(config_location, config_target_location)
    with open(config_target_location, 'r') as infile:
        config_dict = yaml.load(infile.read(), Loader=yaml.SafeLoader)
    return config_dict

