import fv3config
import os
import importlib.resources
import subprocess

def run_scream(config, target_directory):
    os.makedirs(os.path.dirname(target_directory), exist_ok=True)
    local_output_yaml = gather_output_yaml(config["output_yaml"], target_directory)
    config["output_yaml"] = local_output_yaml
    gather_initial_conditions(config["initial_conditions_type"])
    command = compose_commands(config)
    return command

def gather_output_yaml(output_yaml, target_directory):
    local_output_yaml = []
    if isinstance(output_yaml, list):
        for output in output_yaml:
            fv3config.filesystem.get_file(output, os.path.join(target_directory, os.path.basename(output)))
            local_output_yaml.append(os.path.join(target_directory, os.path.basename(output)))
    elif isinstance(output_yaml, str):
        fv3config.filesystem.get_file(output_yaml, os.path.join(target_directory, os.path.basename(output_yaml)))
        local_output_yaml.append(os.path.join(target_directory, os.path.basename(output_yaml)))
    else:
        assert TypeError("output_yaml must be a list of string or a string")
    return local_output_yaml
        
def gather_initial_conditions(initial_conditions_type):
    # TODO: allow initial_conditions_type to be cloud and download all necessary files
    assert initial_conditions_type == "local", \
        "at the moment, initial_conditions_type must already be on disk or \
        mounted through persistentVolume"
        
def compose_commands(config):
    command = ""
    for key, value in config.items():
        if isinstance(value, list):
            value=",".join(value)
        command += f" --{key} {value}"
    return command

def execute_run(command, target_directory):
    run_script = importlib.resources.files("fv3config.scream.template").joinpath("run_eamxx.sh")
    local_script = os.path.join(target_directory, os.path.basename(run_script))
    subprocess.check_call(["cp", str(run_script), local_script])
    command = local_script + command
    print(command)
    subprocess.run(command, shell=True)