import os
from .namelist import config_from_namelist
from ..data import DATA_DIR

DEFAULT_NAMELIST_FILENAME = os.path.join(DATA_DIR, 'namelist/default.nml')
NAMELIST_DEFAULTS = {
    'ntiles': 6,
    'layout': (1, 1),
}


def get_default_config():
    """Returns a default model configuration dictionary."""
    config = {}
    config['namelist'] = config_from_namelist(DEFAULT_NAMELIST_FILENAME)
    config['diag_table'] = 'default'
    config['data_table'] = 'default'
    config['forcing'] = 'default'
    config['initial_conditions'] = 'gfs_example'
    config['experiment_name'] = 'default_experiment'
    return config

