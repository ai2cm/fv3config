import logging
import os
from .._asset_list import write_asset
from .._asset_list_config import config_to_asset_list
from .._tables import update_diag_table_for_config
from .derive import get_time_configuration
from .nudging import enable_nudging
import pathlib

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

    asset_list = config_to_asset_list(config)
    for asset in asset_list:
        write_asset(asset, target_directory)

    os.makedirs(os.path.join(target_directory, "RESTART"), exist_ok=True)

    diag_table = pathlib.Path(target_directory, "diag_table")
    base_date, _ = get_time_configuration(config)
    new_contents = update_diag_table_for_config(
        config, base_date, diag_table.read_text()
    )
    diag_table.write_text(new_contents)
