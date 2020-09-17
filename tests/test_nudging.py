import pytest
from datetime import datetime, timedelta

from fv3config.config import nudging
import fv3config


@pytest.mark.parametrize(
    "start_time, expected",
    [
        (datetime(2016, 1, 1), datetime(2016, 1, 1, 0)),
        (datetime(2016, 1, 1, 1), datetime(2016, 1, 1, 0)),
        (datetime(2016, 1, 1, 7), datetime(2016, 1, 1, 6)),
        (datetime(2016, 1, 1, 12), datetime(2016, 1, 1, 12)),
        (datetime(2016, 1, 2, 18, 1), datetime(2016, 1, 2, 18)),
    ],
)
def test__get_first_nudge_file_time(start_time, expected):
    assert nudging._most_recent_nudge_time(start_time) == expected


@pytest.mark.parametrize(
    "duration, current_date, expected_length, "
    "expected_first_datetime, expected_last_datetime",
    [
        (
            timedelta(days=1),
            [2016, 1, 1, 0, 0, 0],
            4 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2),
        ),
        (
            timedelta(days=1, hours=5),
            [2016, 1, 1, 0, 0, 0],
            4 + 1 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2, 6),
        ),
        (
            timedelta(days=1, hours=7),
            [2016, 1, 1, 0, 0, 0],
            4 + 2 + 1,
            datetime(2016, 1, 1),
            datetime(2016, 1, 2, 12),
        ),
        (
            timedelta(days=1),
            [2016, 1, 2, 1, 0, 0],
            4 + 2,
            datetime(2016, 1, 2),
            datetime(2016, 1, 3, 6),
        ),
    ],
)
def test__get_nudge_time_list(
    duration,
    current_date,
    expected_length,
    expected_first_datetime,
    expected_last_datetime,
):
    nudge_file_list = nudging._get_nudge_time_list(duration, current_date)
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


def test_get_nudging_assets_raises_config_error():
    with pytest.raises(fv3config.ConfigError):
        fv3config.get_nudging_assets(
            timedelta(hours=6),
            [2016, 1, 1, 0, 0, 0],
            "gs://bucket/path",
            copy_method="link",
        )


def test_clear_nudging_assets():
    pattern = "%Y%m%d_%H.nc"
    nudging_asset_1 = fv3config.get_asset_dict("/path", "20160101_00.nc")
    nudging_asset_2 = fv3config.get_asset_dict("/path", "20160101_06.nc")
    non_nudging_asset_1 = fv3config.get_asset_dict("/path", "not nudging file")
    non_nudging_asset_2 = fv3config.get_asset_dict("/path", "also not nudging file")
    input_assets = [
        non_nudging_asset_1,
        nudging_asset_1,
        nudging_asset_2,
        non_nudging_asset_2,
    ]
    cleared_assets = nudging._non_nudging_assets(input_assets, pattern)
    assert non_nudging_asset_1 in cleared_assets
    assert non_nudging_asset_2 in cleared_assets
    assert nudging_asset_1 not in cleared_assets
    assert nudging_asset_2 not in cleared_assets


@pytest.mark.parametrize(
    "target_name, pattern, expected",
    [
        ("20160101_00.nc", "%Y%m%d_%H.nc", True),
        ("20160101_06.nc", "%Y%m%d_%H.nc", True),
        ("not_nudging_file", "%Y%m%d_%H.nc", False),
    ],
)
def test__target_name_matches(target_name, pattern, expected):
    asset = fv3config.get_asset_dict("/path", target_name)
    assert nudging._target_name_matches(asset, pattern) == expected


def test_update_config_for_nudging():
    url = "/path/to/nudging/files"
    pattern = "%Y%m%d_%H.nc"
    old_nudging_file = "20151231_18.nc"
    new_nudging_file = "20160101_06.nc"
    old_asset = fv3config.get_asset_dict(url, old_nudging_file, target_location="INPUT")
    new_asset = fv3config.get_asset_dict(url, new_nudging_file, target_location="INPUT")
    test_config = {
        "gfs_analysis_data": {"url": url, "filename_pattern": pattern},
        "initial_conditions": "/path/to/initial_conditions",
        "namelist": {
            "coupler_nml": {"current_date": [2016, 1, 1, 0, 0, 0], "hours": 12},
            "fv_nwp_nudge_nml": {"file_names": [f"INPUT/{old_nudging_file}"]},
        },
        "patch_files": [old_asset],
    }

    fv3config.update_config_for_nudging(test_config)

    updated_file_names = test_config["namelist"]["fv_nwp_nudge_nml"]["file_names"]
    assert f"INPUT/{old_nudging_file}" not in updated_file_names
    assert f"INPUT/{new_nudging_file}" in updated_file_names
    assert old_asset not in test_config["patch_files"]
    assert new_asset in test_config["patch_files"]
