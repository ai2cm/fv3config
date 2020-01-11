import os
import tarfile
import shutil
import logging
import tempfile
import requests

from fv3config.cache_location import get_internal_cache_dir
from fv3config.config.derive import get_resolution
from fv3config.data import DATA_DIR
from ._exceptions import ConfigError, DataMissingError
from . import filesystem


ARCHIVE_FILENAME = "2019-10-23-data-for-running-fv3gfs.tar.gz"
ARCHIVE_FILENAME_ROOT = "2019-10-23-data-for-running-fv3gfs"
ARCHIVE_URL = f"http://storage.googleapis.com/vcm-ml-public/{ARCHIVE_FILENAME}"

FORCING_OPTIONS_DICT = {
    "default": "base_forcing",
}

INITIAL_CONDITIONS_OPTIONS_DICT = {
    "gfs_example": "initial_conditions/gfs_initial_conditions",
    "restart_example": "initial_conditions/restart_initial_conditions",
}

DATA_TABLE_OPTIONS = {
    "default": os.path.join(DATA_DIR, "data_table/data_table_default"),
}
DIAG_TABLE_OPTIONS = {
    "default": os.path.join(DATA_DIR, "diag_table/diag_table_default"),
    "no_output": os.path.join(DATA_DIR, "diag_table/diag_table_no_output"),
    "grid_spec": os.path.join(DATA_DIR, "diag_table/diag_table_grid_spec"),
}
FIELD_TABLE_OPTIONS = {
    "GFDLMP": os.path.join(DATA_DIR, "field_table/field_table_GFDLMP"),
    "ZhaoCarr": os.path.join(DATA_DIR, "field_table/field_table_ZhaoCarr"),
}


def get_orographic_forcing_directory(config):
    """Return the string path of the orographic forcing directory
    specified by a config dictionary.
    """
    resolution = get_resolution(config)
    dirname = os.path.join(get_internal_cache_dir(), f"orographic_data/{resolution}")
    if not os.path.isdir(dirname):
        valid_options = os.listdir(
            os.path.join(get_internal_cache_dir(), "orographic_data")
        )
        raise ConfigError(
            f"resolution {resolution} is unsupported; valid options are {valid_options}"
        )
    return dirname


def get_base_forcing_directory(config):
    """Return the string path of the base forcing directory
    specified by a config dictionary.
    """
    if "forcing" not in config:
        raise ConfigError("config dictionary must have a 'forcing' key")
    return resolve_option(config["forcing"], FORCING_OPTIONS_DICT)


def get_initial_conditions_directory(config):
    """Return the string path of the initial conditions directory
    specified by a config dictionary.
    """
    if "initial_conditions" not in config:
        raise ConfigError("config dictionary must have an 'initial_conditions' key")
    return resolve_option(config["initial_conditions"], INITIAL_CONDITIONS_OPTIONS_DICT)


def check_if_data_is_downloaded():
    dirname = get_internal_cache_dir()
    if not os.path.isdir(dirname) or len(os.listdir(dirname)) == 0:
        raise DataMissingError(
            "Required data for running fv3gfs not available. Try "
            "python -m fv3config.download_data or ensure_data_is_downloaded()"
        )


def ensure_data_is_downloaded():
    """Check of the cached data is present, and if not, download it."""
    os.makedirs(get_internal_cache_dir(), exist_ok=True)
    if len(os.listdir(get_internal_cache_dir())) == 0:
        with tempfile.NamedTemporaryFile(mode="wb") as archive_file:
            download_data_archive(archive_file)
            archive_file.flush()
            extract_data(archive_file.name)


def refresh_downloaded_data():
    """Delete the cached data (if present) and re-download it."""
    shutil.rmtree(get_internal_cache_dir())
    ensure_data_is_downloaded()


def download_data_archive(target_file):
    """Download the cached data."""
    logging.info("Downloading required data for running fv3gfs to temporary file")
    r = requests.get(ARCHIVE_URL)
    target_file.write(r.content)


def extract_data(archive_filename):
    """Extract the downloaded archive, over-writing any data already present."""
    logging.info(
        "Extracting required data for running fv3gfs to %s", get_internal_cache_dir()
    )
    with tarfile.open(archive_filename, mode="r:gz") as f:
        with tempfile.TemporaryDirectory() as tempdir:
            f.extractall(tempdir)
            for name in os.listdir(os.path.join(tempdir, ARCHIVE_FILENAME_ROOT)):
                shutil.move(
                    os.path.join(tempdir, ARCHIVE_FILENAME_ROOT, name),
                    get_internal_cache_dir(),
                )


def resolve_option(option, built_in_options_dict):
    """Determine whether a configuration dictionary option is a built-in option or
    not and return path to file or directory representing option. An option is
    assumed to be built-in if it is not an absolute path and does not begin with gs://

    Args:
        option (str): an option
        built_in_options_dict (dict): built-in options

    Returns:
        (str): a path or url

    Raises:
        ConfigError: if option is an absolute path but does not exist or if
                     option is not in default_options_dict
    """
    if filesystem.isabs(option):
        if filesystem.get_fs(option).exists(option):
            return option
        else:
            raise ConfigError(f"The provided path {option} does not exist.")
    else:
        if option in built_in_options_dict:
            return os.path.join(get_internal_cache_dir(), built_in_options_dict[option])
        else:
            raise ConfigError(
                f"The provided option {option} is not one of the built in options: "
                f"{list(built_in_options_dict.keys())}. "
                "Paths to local files or directories must be absolute."
            )


def get_microphysics_name(config):
    """Get name of microphysics scheme from configuration dictionary

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: name of microphysics scheme

    Raises:
        NotImplementedError: no microphysics name defined for specified
            imp_physics and ncld combination
    """
    imp_physics = config["namelist"]["gfs_physics_nml"].get("imp_physics")
    ncld = config["namelist"]["gfs_physics_nml"].get("ncld")
    if imp_physics == 11 and ncld == 5:
        microphysics_name = "GFDLMP"
    elif imp_physics == 99 and ncld == 1:
        microphysics_name = "ZhaoCarr"
    else:
        raise NotImplementedError(
            f"Microphysics choice imp_physics={imp_physics} and ncld={ncld} not one of the valid options"
        )
    return microphysics_name


def get_field_table_filename(config):
    """Get field_table filename given configuration dictionary

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: field_table filename

    Raises:
        NotImplementedError: if field_table for microphysics option specified
            in config has not been implemented
    """
    microphysics_name = get_microphysics_name(config)
    if microphysics_name in FIELD_TABLE_OPTIONS.keys():
        filename = FIELD_TABLE_OPTIONS[microphysics_name]
    else:
        raise NotImplementedError(
            f"Field table does not exist for {microphysics_name} microphysics"
        )
    return filename


def get_diag_table_filename(config):
    """Return filename for diag_table specified in config

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: diag_table filename
    """
    if "diag_table" not in config:
        raise ConfigError("config dictionary must have a 'diag_table' key")
    return resolve_option(config["diag_table"], DIAG_TABLE_OPTIONS)


def get_data_table_filename(config):
    """Return filename for data_table specified in config

    Args:
        config (dict): a configuration dictionary

    Returns:
        str: data_table filename
    """
    if "data_table" not in config:
        raise ConfigError("config dictionary must have a 'data_table' key")
    return resolve_option(config["data_table"], DATA_TABLE_OPTIONS)
