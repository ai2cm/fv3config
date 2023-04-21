from copy import deepcopy
import yaml
from typing import Mapping, Any, TextIO


Config = Mapping[str, Any]
def load(f: TextIO) -> Config:
    """Load a configuration from a file-like object f"""
    config = yaml.safe_load(f)    
    return config


def dump(config: Config, f: TextIO):
    """Serialize config to a file-like object using yaml encoding

    Args:
        config: an screamConfig object
        f: the file like object to write to

    """
    config_copy = deepcopy(config)
    yaml.safe_dump(config_copy, f)
