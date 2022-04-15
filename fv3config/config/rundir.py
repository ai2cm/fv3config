import logging
import os
from .._asset_list import write_asset
from .._asset_list_config import config_to_asset_list

logger = logging.getLogger("fv3config")


def write_run_directory(config, target_directory):
    """Write a run directory based on a configuration dictionary.

    Args:
        config (dict): a configuration dictionary
        target_directory (str): target directory, will be created if it does not exist
    """
    logger.debug(f"Writing run directory to {target_directory}")
    asset_list = config_to_asset_list(config)

    for asset in asset_list:
        write_asset(asset, target_directory)

    os.makedirs(os.path.join(target_directory, "RESTART"), exist_ok=True)
