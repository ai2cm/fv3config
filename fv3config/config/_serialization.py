from copy import deepcopy
import yaml
from typing import TextIO

from .types import Config
from .diag_table import DiagTable


def load(f: TextIO) -> Config:
    """Load a configuration from a file-like object f"""
    config = yaml.safe_load(f)
    if isinstance(config["diag_table"], dict):
        config["diag_table"] = DiagTable.from_dict(config["diag_table"])
    return config


def dump(config: Config, f: TextIO):
    """Serialize config to a file-like object using yaml encoding

    Args:
        config: an fv3config object
        f: the file like object to write to

    """
    config_copy = deepcopy(config)
    if isinstance(config["diag_table"], DiagTable):
        config_copy["diag_table"] = config["diag_table"].asdict()
    yaml.safe_dump(config_copy, f)
