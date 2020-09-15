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
    input_fname = "file_list"
    file_list = b"20160101_00.nc\n20160101_06.nc"
    assets = fv3config.get_nudging_assets(
        timedelta(hours=6),
        [2016, 1, 1, 0, 0, 0],
        nudge_url,
        nudge_filename_pattern=pattern,
        input_list_filename=input_fname,
    )
    expected = [
        fv3config.get_asset_dict(nudge_url, "20160101_00.nc", target_location="INPUT"),
        fv3config.get_asset_dict(nudge_url, "20160101_06.nc", target_location="INPUT"),
        fv3config.get_bytes_asset_dict(file_list, "", input_fname),
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
    data = b"20160101_00.nc\n20160101_06.nc"
    pattern = "%Y%m%d_%H.nc"
    input_fname = "file_list"
    nudging_asset_1 = fv3config.get_asset_dict("/path", "20160101_00.nc")
    nudging_asset_2 = fv3config.get_asset_dict("/path", "20160101_06.nc")
    non_nudging_asset = fv3config.get_asset_dict("/path", "not nudging file")
    nudging_bytes_asset = fv3config.get_bytes_asset_dict(data, "", input_fname)
    non_nudging_bytes_asset = fv3config.get_bytes_asset_dict(
        data, "", "not nudging bytes assets"
    )
    input_assets = [
        nudging_asset_1,
        nudging_asset_2,
        non_nudging_asset,
        nudging_bytes_asset,
        non_nudging_bytes_asset,
    ]
    cleared_assets = fv3config.clear_nudging_assets(input_assets, pattern, input_fname)
    assert non_nudging_asset in cleared_assets
    assert non_nudging_bytes_asset in cleared_assets
    assert nudging_asset_2 not in cleared_assets
    assert nudging_asset_1 not in cleared_assets
    assert nudging_bytes_asset not in cleared_assets


@pytest.mark.parametrize(
    "target_name, pattern, exact_match, expected",
    [
        ("20160101_00.nc", "%Y%m%d_%H.nc", "file.txt", True),
        ("20160101_06.nc", "%Y%m%d_%H.nc", "file.txt", True),
        ("not_nudging_file", "%Y%m%d_%H.nc", "file.txt", False),
        ("file.txt", "%Y%m%d_%H.nc", "file.txt", True),
    ],
)
def test__target_name_matches(target_name, pattern, exact_match, expected):
    asset = fv3config.get_asset_dict("/path", target_name)
    assert nudging._target_name_matches(asset, pattern, exact_match) == expected
