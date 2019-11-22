import os
from ._docker import _run_in_docker
from ._native import _run_native


def run(config_dict_or_location, outdir, runfile=None, docker_image=None, keyfile=None):
    """Run the FV3GFS model with the given configuration.

    Copies the resulting directory to a target location. Will use the Google cloud
    storage key at $GOOGLE_APPLICATION_CREDENTIALS by default. Requires the
    fv3gfs-python package.

    Args:
        config_dict_or_location (dict or str): a configuration dictionary, or a
            location (local or on Google cloud storage) of a yaml file containing
            a configuration dictionary
        outdir (str): location to copy the resulting run directory
        runfile (str, optional): Python model script to use in place of the default.
        docker_image (str, optional): If given, run this command inside a container
            using this docker image. Image must have this package and fv3gfs-python
            installed.
        keyfile (str, optional): location of a Google cloud storage key
    """
    if keyfile is None:
        keyfile = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', None)
    if docker_image is not None:
        _run_in_docker(
            config_dict_or_location, outdir, docker_image,
            runfile=runfile, keyfile=keyfile
        )
    else:
        _run_native(config_dict_or_location, outdir, runfile=runfile)
