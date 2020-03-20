import tempfile
import subprocess
import os
from .. import filesystem
from ._native import CONFIG_OUT_FILENAME, _get_config_dict_and_write, run_native

DOCKER_OUTDIR = "/outdir"
DOCKER_CONFIG_LOCATION = os.path.join("/", CONFIG_OUT_FILENAME)
DOCKER_RUNFILE = "/runfile.py"
DOCKER_COMMAND = ["docker", "run"]
DOCKER_KEYFILE = "/gcs_key.json"
FV3RUN_MODULE = "fv3config.fv3run"


def run_docker(
    config_dict_or_location, outdir, docker_image, runfile=None, keyfile=None,
    **kwargs
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
    bind_mount_args = []
    docker_args = []
    _get_docker_args(docker_args, bind_mount_args, outdir)
    _get_credentials_args(keyfile, docker_args, bind_mount_args)
    runfile = _get_runfile_args(runfile, bind_mount_args)
    python_command = run_native.command(config_dict_or_location, outdir, runfile=runfile)
    subprocess.check_call(
        DOCKER_COMMAND
        + bind_mount_args
        + docker_args
        + [docker_image]
        + python_command
    )


def _get_runfile_args(runfile, bind_mount_args) -> str:
    if runfile is not None:
        if filesystem._is_local_path(runfile):
            bind_mount_args += ["-v", f"{os.path.abspath(runfile)}:{DOCKER_RUNFILE}"]
            return DOCKER_RUNFILE
        else:
            return runfile


def _get_config_args(config_dict_or_location, config_tempfile, bind_mount_args):
    config_dict = _get_config_dict_and_write(
        config_dict_or_location, config_tempfile.name
    )
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
        bind_mount_args += ["-v", f"{config_tempfile.name}:{DOCKER_CONFIG_LOCATION}"]
        config_location = DOCKER_CONFIG_LOCATION
    _get_local_data_bind_mounts(config_dict, bind_mount_args)
    return config_location


def _get_paths(config_dict):
    """Return a list of all paths referenced by the config dict."""
    return_list = [
        config_dict["diag_table"],
        config_dict["data_table"],
        config_dict["forcing"],
        config_dict["initial_conditions"],
    ]
    patch_files = config_dict.get("patch_files", [])
    if isinstance(patch_files, list):
        return_list.extend(patch_files)
    else:
        return_list.append(patch_files)
    return return_list


def _is_local_path(maybe_path_or_object):
    return (
        isinstance(maybe_path_or_object, str)
        and os.path.isabs(maybe_path_or_object)
        and filesystem._is_local_path(maybe_path_or_object)
    )


def _get_local_data_paths(config_dict):
    """Return a list of all local paths referenced by the config dict."""
    local_paths = []
    for potential_path in _get_paths(config_dict):
        if _is_local_path(potential_path):
            local_paths.append(potential_path)
        elif isinstance(potential_path, list):
            for asset in potential_path:
                if filesystem._is_local_path(asset["source_location"]):
                    local_paths.append(
                        os.path.join(asset["source_location"], asset["source_name"])
                    )
        elif isinstance(potential_path, dict):
            asset = potential_path
            if filesystem._is_local_path(asset["source_location"]):
                local_paths.append(
                    os.path.join(asset["source_location"], asset["source_name"])
                )
    return local_paths


def _get_local_data_bind_mounts(config_dict, bind_mount_args):
    for local_path in _get_local_data_paths(config_dict):
        bind_mount_args += ["-v", f"{local_path}:{local_path}"]


def _get_docker_args(docker_args, bind_mount_args, outdir):
    bind_mount_args += ["-v", f"{os.path.abspath(outdir)}:{DOCKER_OUTDIR}"]
    docker_args += ["--rm", "--user", f"{os.getuid()}:{os.getgid()}"]


def _get_credentials_args(keyfile, docker_args, bind_mount_args):
    if keyfile is not None:
        bind_mount_args += ["-v", f"{os.path.abspath(keyfile)}:{DOCKER_KEYFILE}"]
        docker_args += ["-e", f"GOOGLE_APPLICATION_CREDENTIALS={DOCKER_KEYFILE}"]
