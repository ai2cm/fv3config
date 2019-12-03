import fv3config

config = fv3config.get_default_config()
config['initial_conditions'] = (
    "gs://vcm-ml-data/2019-10-28-X-SHiELD-2019-10-05-multiresolution-extracted/"
    "restart/C48/20160801.003000/rundir/INPUT")
fv3config.write_run_directory(config, "example_rundir_from_remote")
