from datetime import datetime, timedelta
from functools import partial
import os
from typing import Sequence, List, Mapping
import math
import fsspec
from .._asset_list import get_asset_dict
from .._exceptions import ConfigError
from ..filesystem import get_fs
from .derive import get_current_date, get_run_duration

# this module assumes that analysis files are at 00Z, 06Z, 12Z and 18Z
SECONDS_IN_HOUR = 60 * 60
NUDGE_HOURS = [0, 6, 12, 18]  # hours at which analysis data is available


def _most_recent_nudge_time(start_time: datetime) -> datetime:
    """Return datetime object for the last nudging time preceding or concurrent
     with start_time"""
    first_nudge_hour = _most_recent_hour(start_time.hour)
    return datetime(start_time.year, start_time.month, start_time.day, first_nudge_hour)


def _most_recent_hour(current_hour: int, hour_array=NUDGE_HOURS) -> int:
    """Return latest hour in hour_array that precedes or is concurrent with
    current_hour"""
    for hour in hour_array:
        if hour <= current_hour:
            first_nudge_hour = hour
    return first_nudge_hour


def _get_nudge_time_list(run_duration, current_date) -> List[datetime]:
    """Return list of datetime objects corresponding to times at which analysis files
    are required for nudging for a given model run configuration"""
    start_time = datetime(*current_date)
    first_nudge_time = _most_recent_nudge_time(start_time)
    nudge_duration = run_duration + (start_time - first_nudge_time)
    nudge_duration_hours = int(
        math.ceil(nudge_duration.total_seconds() / SECONDS_IN_HOUR)
    )
    nudge_interval = NUDGE_HOURS[1] - NUDGE_HOURS[0]
    nudging_hours = range(0, nudge_duration_hours + nudge_interval, nudge_interval)
    return [first_nudge_time + timedelta(hours=hour) for hour in nudging_hours]


def get_nudging_assets(
    run_duration: timedelta,
    current_date: Sequence[int],
    nudge_url: str,
    nudge_filename_pattern: str = "%Y%m%d_%HZ_T85LR.nc",
    copy_method: str = "copy",
) -> List[Mapping]:
    """Return list of assets of all nudging files as well as an asset for the text file
    that describes the nudging files (required by fv3gfs to read the nudging files).
    
    Args:
        run_duration: length of fv3gfs run
        current_date: start date of fv3gfs run as a sequence of 6 integers
        nudge_url: local or remote path to nudging files
        nudge_filename_pattern: template for nudging filenames. Defaults to
            '%Y%m%d_%HZ_T85LR.nc'.
        copy_method: copy_method for nudging file assets. Defaults to 'copy'.

    Returns:
        list of all assets required for nudging run

    Raises:
        ConfigError: if a remote path is given for nudge_url and copy_method="link"
    """
    if get_fs(nudge_url) != fsspec.filesystem("file") and copy_method == "link":
        raise ConfigError(
            "Cannot link nudging files if using remote path for nudge_url. "
            f"Got {nudge_url}."
        )
    time_list = _get_nudge_time_list(run_duration, current_date)
    filename_list = [time.strftime(nudge_filename_pattern) for time in time_list]
    nudging_assets = [
        get_asset_dict(
            nudge_url, file_, target_location="INPUT", copy_method=copy_method
        )
        for file_ in filename_list
    ]
    return nudging_assets


def _non_nudging_assets(
    assets: Sequence[Mapping], nudge_filename_pattern: str,
) -> List[Mapping]:
    """Given list of assets, return filtered list with no nudging assets.

    Args:
        assets: sequence of assets
        nudge_filename_pattern: datetime pattern of nudging files. Defaults to
            '%Y%m%d_%HZ_T85LR.nc'.
        input_list_filename: name of text file listing all nudging files. Defaults to
            'nudging_file_list'.
    """
    is_nudging_asset = partial(_target_name_matches, pattern=nudge_filename_pattern)
    return [item for item in assets if not is_nudging_asset(item)]


def _target_name_matches(asset, pattern):
    target_name = asset["target_name"]
    try:
        datetime.strptime(target_name, pattern)
        return True
    except ValueError:
        # target_name does not fit given pattern
        return False


def update_config_for_nudging(config, nudge_url, nudge_filename_pattern, copy_method):
    """Update config object in place to include up-to-date nudging file assets"""
    if "patch_files" in config:
        config["patch_files"] = _non_nudging_assets(
            config["patch_files"], nudge_filename_pattern
        )

    nudging_file_assets = get_nudging_assets(
        get_run_duration(config),
        get_current_date(config),
        nudge_url,
        nudge_filename_pattern=nudge_filename_pattern,
        copy_method=copy_method,
    )

    target_file_paths = [
        os.path.join(asset["target_location"], asset["target_name"])
        for asset in nudging_file_assets
    ]

    config["namelist"]["fv_nwp_nudge_nml"]["file_names"] = target_file_paths
    config.setdefault("patch_files", []).extend(nudging_file_assets)
