import tempfile
import subprocess
import os
from .. import filesystem
from ..config import config_to_yaml
from ._native import CONFIG_OUT_FILENAME

DOCKER_OUTDIR = "/outdir"
DOCKER_CONFIG_LOCATION = os.path.join("/", CONFIG_OUT_FILENAME)
DOCKER_RUNFILE = "/runfile.py"
DOCKER_COMMAND = ["docker", "run"]
DOCKER_KEYFILE = "/gcs_key.json"
FV3RUN_MODULE = "fv3config.fv3run"


def run_docker(
    config_dict_or_location, outdir, docker_image, runfile=None, keyfile=None
):
    """Run the FV3GFS model in a docker container with the given configuration.

    Copies the resulting directory to a target location. Will use the Google cloud
    storage key at ``$GOOGLE_APPLICATION_CREDENTIALS`` by default. Requires the
    fv3gfs-python package and fv3config to be installed in the docker image.

    Args:
        config_dict_or_location (dict or str): a configuration dictionary, or a
            location (local or on Google cloud storage) of a yaml file containing
            a configuration dictionary
        outdir (str): location to copy the resulting run directory
        runfile (str, optional): Python model script to use in place of the default.
        docker_image (str, optional): If given, run this command inside a container
            using this docker image. Image must have this package and fv3gfs-python
            installed.
        keyfile (str, optional): location of a Google cloud storage key to use
            inside the docker container
    """
    if keyfile is None:
        keyfile = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", None)
    filesystem.get_fs(outdir).makedirs(outdir, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".yaml") as config_tempfile:
        bind_mount_args = []
        python_args = []
        docker_args = []
        config_location = _get_config_args(
            config_dict_or_location, config_tempfile, bind_mount_args
        )
        _get_docker_args(docker_args, bind_mount_args, outdir)
        _get_credentials_args(keyfile, docker_args, bind_mount_args)
        _get_runfile_args(runfile, bind_mount_args, python_args)
        python_command = _get_python_command(config_location, DOCKER_OUTDIR)
        subprocess.check_call(
            DOCKER_COMMAND
            + bind_mount_args
            + docker_args
            + [docker_image]
            + python_command
            + python_args
        )


def _get_runfile_args(runfile, bind_mount_args, python_args):
    if runfile is not None:
        if filesystem._is_local_path(runfile):
            bind_mount_args += ["-v", f"{os.path.abspath(runfile)}:{DOCKER_RUNFILE}"]
            python_args += ["--runfile", DOCKER_RUNFILE]
        else:
            python_args += ["--runfile", runfile]


def _get_python_command(config_location, outdir):
    return ["python3", "-m", FV3RUN_MODULE, config_location, outdir]


def _get_config_args(config_dict_or_location, config_tempfile, bind_mount_args):
    if isinstance(config_dict_or_location, str):
        if filesystem._is_local_path(config_dict_or_location):
            bind_mount_args += [
                "-v",
                f"{os.path.abspath(config_dict_or_location)}:{DOCKER_CONFIG_LOCATION}",
            ]
            config_location = DOCKER_CONFIG_LOCATION
        else:
            config_location = config_dict_or_location
    else:
        config_to_yaml(config_dict_or_location, config_tempfile.name)
        bind_mount_args += ["-v", f"{config_tempfile.name}:{DOCKER_CONFIG_LOCATION}"]
        config_location = DOCKER_CONFIG_LOCATION
    return config_location


def _get_docker_args(docker_args, bind_mount_args, outdir):
    bind_mount_args += ["-v", f"{os.path.abspath(outdir)}:{DOCKER_OUTDIR}"]
    docker_args += ["--rm", "--user", f"{os.getuid()}:{os.getgid()}"]


def _get_credentials_args(keyfile, docker_args, bind_mount_args):
    if keyfile is not None:
        bind_mount_args += ["-v", f"{os.path.abspath(keyfile)}:{DOCKER_KEYFILE}"]
        docker_args += ["-e", f"GOOGLE_APPLICATION_CREDENTIALS={DOCKER_KEYFILE}"]
