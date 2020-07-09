import fv3config
import yaml

with open("c12_config.yml", "r") as f:
    config = yaml.safe_load(f)
fv3config.write_run_directory(config, "example_rundir_from_remote")
