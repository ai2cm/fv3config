import argparse

import yaml
import fsspec

import fv3config


def _parse_args():
    parser = argparse.ArgumentParser("write_run_directory")
    parser.add_argument(
        "config", help="URI to fv3config yaml file. Supports any path used by fsspec."
    )
    parser.add_argument(
        "rundir", help="Desired output directory. Must be a local directory"
    )
    return parser.parse_args()


def write_run_directory():
    args = _parse_args()

    with fsspec.open(args.config) as f:
        config = yaml.safe_load(f)

    fv3config.write_run_directory(config, args.rundir)
