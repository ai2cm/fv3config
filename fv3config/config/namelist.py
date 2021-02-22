from copy import deepcopy
import os
import f90nml
import fsspec
import yaml
from .._exceptions import InvalidFileError
from .diag_table import DiagTable


def config_to_yaml(config, config_out_filename):
    config_copy = deepcopy(config)
    if isinstance(config["diag_table"], DiagTable):
        config_copy["diag_table"] = config["diag_table"].asdict()
    with fsspec.open(config_out_filename, "w") as outfile:
        outfile.write(yaml.dump(config_copy))


def config_from_yaml(path):
    """Return fv3config dictionary at path"""
    with fsspec.open(path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    if isinstance(config["diag_table"], dict):
        config["diag_table"] = DiagTable.from_dict(config["diag_table"])
    return config


def config_to_namelist(config, namelist_filename):
    """Write the namelist of a configuration dictionary to a namelist file.

    Args:
        config (dict): a configuration dictionary
        namelist_filename (str): filename to write, will be overwritten if present
    """
    if os.path.isfile(namelist_filename):
        os.remove(namelist_filename)
    f90nml.write(config["namelist"], namelist_filename)


def config_from_namelist(namelist_filename):
    """Read a configuration dictionary from a namelist file.

    Only reads the namelist configuration.

    Args:
        namelist_filename (str): a namelist filename

    Returns:
        return_dict (dict): a configuration dictionary

    Raises:
        InvalidFileError: if the specified filename does not exist
    """
    try:
        return_dict = _to_nested_dict(f90nml.read(namelist_filename).items())
    except FileNotFoundError:
        raise InvalidFileError(f"namelist {namelist_filename} does not exist")
    return return_dict


def _to_nested_dict(source):
    return_value = dict(source)
    for name, value in return_value.items():
        if isinstance(value, f90nml.Namelist):
            return_value[name] = _to_nested_dict(value)
    return return_value
