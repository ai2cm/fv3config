import sys
import argparse
from ._run import run

MODULE_NAME = 'fv3config.run'
# RESTART_DIR_PATTERN = "gs://vcm-ml-data/2019-10-28-X-SHiELD-2019-10-05-multiresolution-extracted/restart/C48/{time}/rundir"
# OUTPUT_DIR_PATTERN = "gs://vcm-ml-data/2019-10-28-X-SHiELD-2019-10-05-multiresolution-extracted/one-step-run/C48/{time}/rundir"
STDOUT_FILENAME = 'stdout.log'
STDERR_FILENAME = 'stderr.log'
DOCKER_FLAGS = '-it'


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Run the FV3GFS model.

Will use google cloud storage key at $GOOGLE_APPLICATION_CREDENTIALS by default.
"""
    )
    parser.add_argument('config', type=str, action='store', help='location of fv3config yaml file')
    parser.add_argument('outdir', type=str, action='store', help='location to copy final run directory')
    parser.add_argument('--runfile', type=str, action='store', help='location of python script to execute with mpirun')
    parser.add_argument('--dockerimage', type=str, action='store', help='if passed, execute inside a docker image with the given name')
    parser.add_argument('--keyfile', type=str, action='store', help='google cloud storage key to use for cloud copy commands')
    return parser.parse_args()


def main():
    """Run the FV3GFS model one step forward for the run-directory for a specific time

    Args:
        time: the timestep YYYYMMDD.HHMMSS to run the model for
        rundir_transformations: a sequence of transformations (e.g. modifying the diag_table) to
           apply to the downloaded run directory before the FV3 simulation.

    """
    args = _parse_args()
    run(args.config, args.outdir, args.runfile, args.dockerimage, args.keyfile)


if __name__ == '__main__':
    sys.exit(main())
