import os
import importlib.resources
import subprocess
from .config import ScreamConfig
from dataclasses import asdict


def compose_run_scream_commands(config: ScreamConfig, target_directory: str):
    os.makedirs(os.path.dirname(target_directory), exist_ok=True)
    command = ""
    for key, value in asdict(config).items():
        if isinstance(value, list):
            value = ",".join(value)
        command += f" --{key} {value}"
    return command


def execute_run(command, target_directory: str):
    run_script = importlib.resources.files("fv3config.scream.template").joinpath(
        "run_eamxx.sh"
    )
    local_script = os.path.join(target_directory, os.path.basename(run_script))
    subprocess.check_call(["cp", str(run_script), local_script])
    command = local_script + command
    subprocess.run(command, shell=True)
