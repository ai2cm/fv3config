import argparse
import fsspec

import fv3config
import logging


def _parse_write_run_directory_args():
    parser = argparse.ArgumentParser("write_run_directory")
    parser.add_argument(
        "config", help="URI to fv3config yaml file. Supports any path used by fsspec."
    )
    parser.add_argument(
        "rundir", help="Desired output directory. Must be a local directory"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output."
    )
    return parser.parse_args()


def _parse_enable_restart_args():
    parser = argparse.ArgumentParser("enable_restart")
    parser.add_argument(
        "config",
        help="URI to fv3config yaml file. Supports any path used by fsspec. "
        "File will be modified in place.",
    )
    parser.add_argument(
        "initial_conditions", help="Path to restart initial conditions.",
    )
    return parser.parse_args()


def _parse_enable_nudging_args():
    parser = argparse.ArgumentParser("enable_nudging")
    parser.add_argument(
        "config",
        help="URI to fv3config yaml file. Supports any path used by fsspec. "
        "File will be modified in place.",
    )
    return parser.parse_args()


def write_run_directory():
    args = _parse_write_run_directory_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    with fsspec.open(args.config) as f:
        config = fv3config.load(f)

    fv3config.write_run_directory(config, args.rundir)


def enable_restart():
    args = _parse_enable_restart_args()

    with fsspec.open(args.config) as f:
        config = fv3config.load(f)

    restart_config = fv3config.enable_restart(config, args.initial_conditions)

    with fsspec.open(args.config, mode="w") as f:
        fv3config.dump(restart_config, f)


def enable_nudging():
    args = _parse_enable_nudging_args()

    with fsspec.open(args.config) as f:
        config = fv3config.load(f)

    # only update config if nudging is turned on
    if config["namelist"]["fv_core_nml"].get("nudge", False):
        updated_config = fv3config.enable_nudging(config)

        with fsspec.open(args.config, mode="w") as f:
            fv3config.dump(updated_config, f)
