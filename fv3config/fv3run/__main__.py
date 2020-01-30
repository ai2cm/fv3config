import sys
import argparse
from ._docker import run_docker
from ._native import run_native, RUNFILE_ENV_VAR

MODULE_NAME = "fv3config.run"
STDOUT_FILENAME = "stdout.log"
STDERR_FILENAME = "stderr.log"
DOCKER_FLAGS = "-it"


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Run the FV3GFS model.

Will use google cloud storage key at $GOOGLE_APPLICATION_CREDENTIALS by default.
"""
    )
    parser.add_argument(
        "config", type=str, action="store", help="location of fv3config yaml file"
    )
    parser.add_argument(
        "outdir", type=str, action="store", help="location to copy final run directory"
    )
    parser.add_argument(
        "--runfile",
        type=str,
        action="store",
        help="Location of python script to execute with mpirun. If not specified, a "
        f"default is used, which can be overriden by setting the {RUNFILE_ENV_VAR}.",
    )
    parser.add_argument(
        "--dockerimage",
        type=str,
        action="store",
        help="if passed, execute inside a docker image with the given name",
    )
    parser.add_argument(
        "--keyfile",
        type=str,
        action="store",
        help="google cloud storage key to use for cloud copy commands",
    )
    return parser.parse_args()


def main():
    """Run the FV3GFS model based on a configuration dictionary.
    Copies the resulting run directory to a target location.
    """
    args = _parse_args()
    run(args.config, args.outdir, args.runfile, args.dockerimage, args.keyfile)


def run(config_dict_or_location, outdir, runfile=None, docker_image=None, keyfile=None):
    """Run the FV3GFS model with the given configuration.

    Copies the resulting directory to a target location. Will use the Google cloud
    storage key at ``$GOOGLE_APPLICATION_CREDENTIALS`` by default. Requires the
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
    if docker_image is not None:
        run_docker(
            config_dict_or_location,
            outdir,
            docker_image,
            runfile=runfile,
            keyfile=keyfile,
        )
    else:
        run_native(config_dict_or_location, outdir, runfile=runfile)


if __name__ == "__main__":
    sys.exit(main())
