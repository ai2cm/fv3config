import argparse
from .loader import load
from .run_scream import run_scream, execute_run
import fsspec

def _parse_run_scream_command_args():
    parser = argparse.ArgumentParser("run_scream_command")
    parser.add_argument(
        "config", help="URI to scream yaml file. Supports any path used by fsspec."
    )
    parser.add_argument(
        "rundir", help="Desired output directory. Must be a local directory"
    )
    return parser.parse_args()
    
def run_scream_command():
    args = _parse_run_scream_command_args()
    with fsspec.open(args.config) as f:
        config = load(f)    
    command = run_scream(config, args.rundir)
    return command

def execute_run_scream():
    args = _parse_run_scream_command_args()
    command = run_scream_command()
    execute_run(command, args.rundir)
    