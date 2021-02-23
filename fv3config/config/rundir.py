import logging
import os
from .namelist import config_to_namelist
from .._asset_list import write_assets_to_directory
from .._tables import update_diag_table_for_config
from .derive import get_current_date
from .nudging import update_config_for_nudging

logger = logging.getLogger("fv3config")


def write_run_directory(config, target_directory):
    """Write a run directory based on a configuration dictionary.

    Args:
        config (dict): a configuration dictionary
        target_directory (str): target directory, will be created if it does not exist
    """
    logger.debug(f"Writing run directory to {target_directory}")
    if "gfs_analysis_data" in config:
        update_config_for_nudging(config)
    write_assets_to_directory(config, target_directory)
    os.makedirs(os.path.join(target_directory, "RESTART"), exist_ok=True)
    current_date = get_current_date(config)
    update_diag_table_for_config(
        config, current_date, os.path.join(target_directory, "diag_table")
    )
    config_to_namelist(config, os.path.join(target_directory, "input.nml"))
