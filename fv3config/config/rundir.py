import logging
import os
from .namelist import config_to_namelist
from .._asset_list import write_assets_to_directory
from .._tables import update_diag_table_for_config
from .derive import get_time_configuration
from .nudging import enable_nudging

logger = logging.getLogger("fv3config")


def write_run_directory(config, target_directory):
    """Write a run directory based on a configuration dictionary.

    Args:
        config (dict): a configuration dictionary
        target_directory (str): target directory, will be created if it does not exist
    """
    logger.debug(f"Writing run directory to {target_directory}")
    if config["namelist"]["fv_core_nml"].get("nudge", False):
        config = enable_nudging(config)
    write_assets_to_directory(config, target_directory)
    os.makedirs(os.path.join(target_directory, "RESTART"), exist_ok=True)
    base_date, _ = get_time_configuration(config)
    update_diag_table_for_config(
        config, base_date, os.path.join(target_directory, "diag_table")
    )
    config_to_namelist(config, os.path.join(target_directory, "input.nml"))
