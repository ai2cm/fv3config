import pytest
from datetime import datetime, timedelta

from fv3config.config import nudging
import fv3config


@pytest.fixture
def test_config(c12_config):
    return c12_config


@pytest.mark.parametrize(
    "start_time, interval, expected",
    [
        (datetime(2016, 1, 1), timedelta(hours=6), datetime(2016, 1, 1, 0)),
        (datetime(2016, 1, 1, 1), timedelta(hours=6), datetime(2016, 1, 1, 0)),
        (datetime(2016, 1, 1, 1), timedelta(hours=2), datetime(2016, 1, 1, 0)),
        (datetime(2016, 1, 1, 3), timedelta(hours=2), datetime(2016, 1, 1, 2)),
        (datetime(2016, 1, 1, 7), timedelta(hours=6), datetime(2016, 1, 1, 6)),
        (datetime(2016, 1, 1, 12), timedelta(hours=6), datetime(2016, 1, 1, 12)),
        (datetime(2016, 1, 2, 18, 1), timedelta(hours=6), datetime(2016, 1, 2, 18)),
    ],
)
def test__get_first_nudge_file_time(start_time, interval, expected):
    assert nudging._most_recent_nudge_time(start_time, interval) == expected


@pytest.mark.parametrize(
    "duration, current_date, interval, expected_length, "
    "expected_first_datetime, expected_last_datetime",
    [
        (
            timedelta(days=1),
            [2016, 1, 1, 0, 0, 0],
            timedelta(hours=6),
            4 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2),
        ),
        (
            timedelta(days=1),
            [2016, 1, 1, 0, 0, 0],
            timedelta(hours=2),
            12 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2),
        ),
        (
            timedelta(days=1, hours=5),
            [2016, 1, 1, 0, 0, 0],
            timedelta(hours=6),
            4 + 1 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2, 6),
        ),
        (
            timedelta(days=1, hours=7),
            [2016, 1, 1, 0, 0, 0],
            timedelta(hours=6),
            4 + 2 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2, 12),
        ),
        (
            timedelta(days=1),
            [2016, 1, 2, 1, 0, 0],
            timedelta(hours=6),
            4 + 2,
            datetime(2016, 1, 2),
            datetime(2016, 1, 3, 6),
        ),
    ],
)
def test__get_nudge_time_list(
    duration,
    current_date,
    interval,
    expected_length,
    expected_first_datetime,
    expected_last_datetime,
):
    nudge_file_list = nudging._get_nudge_time_list(duration, current_date, interval)
    assert len(nudge_file_list) == expected_length
    assert nudge_file_list[0] == expected_first_datetime
    assert nudge_file_list[-1] == expected_last_datetime


def test_get_nudging_assets():
    nudge_url = "/path/to/files"
    pattern = "%Y%m%d_%H.nc"
    assets = fv3config.get_nudging_assets(
        timedelta(hours=6),
        [2016, 1, 1, 0, 0, 0],
        nudge_url,
        nudge_filename_pattern=pattern,
    )
    expected = [
        fv3config.get_asset_dict(nudge_url, "20160101_00.nc", target_location="INPUT"),
        fv3config.get_asset_dict(nudge_url, "20160101_06.nc", target_location="INPUT"),
    ]
    assert assets == expected


def test_get_nudging_assets_raises_config_error_if_linking_remote_files():
    with pytest.raises(fv3config.ConfigError):
        fv3config.get_nudging_assets(
            timedelta(hours=6),
            [2016, 1, 1, 0, 0, 0],
            "gs://bucket/path",
            copy_method="link",
        )


@pytest.mark.parametrize(
    "nudging_assets, other_items, pattern",
    [
        ([], [], "%Y%m%d_%H.nc"),
        ([fv3config.get_asset_dict("/path", "20160101_00.nc")], [], "%Y%m%d_%H.nc"),
        ([], ["non asset item"], "%Y%m%d_%H.nc"),
        ([], [{"other": "non asset item"}], "%Y%m%d_%H.nc"),
        (
            [fv3config.get_asset_dict("/path", "20160101_00.nc")],
            ["non asset item"],
            "%Y%m%d_%H.nc",
        ),
        (
            [fv3config.get_asset_dict("/path", "20160101_00.nc")],
            [fv3config.get_asset_dict("/path", "non nudging asset"), "non asset"],
            "%Y%m%d_%H.nc",
        ),
    ],
)
def test__non_nudging_assets(nudging_assets, other_items, pattern):
    input_assets = nudging_assets + other_items
    cleared_assets = nudging._non_nudging_assets(input_assets, pattern)
    for item in nudging_assets:
        assert item not in cleared_assets
    for item in other_items:
        assert item in cleared_assets


@pytest.mark.parametrize(
    "item, pattern, expected",
    [
        (fv3config.get_asset_dict("/path", "20160101_00.nc"), "%Y%m%d_%H.nc", True),
        (fv3config.get_asset_dict("/path", "not_nudging_file"), "%Y%m%d_%H.nc", False),
    ],
)
def test__is_nudging_asset(item, pattern, expected):
    assert nudging._is_nudging_asset(item, pattern) == expected


def test_update_config_for_nudging(test_config):
    url = "/path/to/nudging/files"
    pattern = "%Y%m%d_%H.nc"
    old_nudging_file = "20151231_18.nc"
    new_nudging_file = "20160101_06.nc"
    old_asset = fv3config.get_asset_dict(url, old_nudging_file, target_location="INPUT")
    new_asset = fv3config.get_asset_dict(url, new_nudging_file, target_location="INPUT")
    test_config["gfs_analysis_data"] = {"url": url, "filename_pattern": pattern}
    test_config["namelist"]["coupler_nml"]["current_date"] = [2016, 1, 1, 0, 0, 0]
    test_config["namelist"]["coupler_nml"]["hours"] = 12
    test_config["namelist"]["fv_nwp_nudge_nml"] = {
        "file_names": [f"INPUT/{old_nudging_file}"]
    }
    test_config["patch_files"] = [old_asset]

    fv3config.update_config_for_nudging(test_config)

    updated_file_names = test_config["namelist"]["fv_nwp_nudge_nml"]["file_names"]
    assert f"INPUT/{old_nudging_file}" not in updated_file_names
    assert f"INPUT/{new_nudging_file}" in updated_file_names
    assert old_asset not in test_config["patch_files"]
    assert new_asset in test_config["patch_files"]
