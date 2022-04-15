import os
from ._exceptions import ConfigError

package_directory = os.path.dirname(os.path.realpath(__file__))


def update_diag_table_for_config(config, base_date, diag_table_contents: str):
    """Re-write first two lines of diag_table_filename with experiment_name
    and base_date from config dictionary.

    Args:
        config (dict): a configuration dictionary
        base_date (list): a list of 6 integers representing base_date
        diag_table_contents (str): the contents of the diag table file
    """
    if "experiment_name" not in config:
        raise ConfigError("config dictionary must have a 'experiment_name' key")

    lines = diag_table_contents.splitlines()
    lines[0] = config["experiment_name"] + "\n"
    lines[1] = " ".join([str(x) for x in base_date]) + "\n"
    return "".join(lines)
