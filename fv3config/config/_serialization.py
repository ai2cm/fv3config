from copy import deepcopy
import yaml

from .types import Config
from .diag_table import DiagTable

import fsspec

def config_to_yaml(config: Config, config_out_filename: str):
    with fsspec.open(config_out_filename, "w") as outfile:
        dump(config, outfile)


def config_from_yaml(path: str) -> Config:
    """Return fv3config dictionary at path"""
    with fsspec.open(path) as yaml_file:
        return load(yaml_file)


def loads(s: str) -> Config:
    import io
    io.StringIO()


def load(f) -> Config:
    """Load a configuration from a file-like object f"""
    config = yaml.safe_load(f)
    if isinstance(config["diag_table"], dict):
        config["diag_table"] = DiagTable.from_dict(config["diag_table"])
    return config


def dump(config: Config, f):
    """Serialize config to a file-like object using yaml encoding

    Args:
        config: an fv3config object
        f: the file like object to write to

    """
    config_copy = deepcopy(config)
    if isinstance(config["diag_table"], DiagTable):
        config_copy["diag_table"] = config["diag_table"].asdict()
    f.write(yaml.dump(config_copy))
