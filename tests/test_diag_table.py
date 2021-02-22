from datetime import datetime
import pytest

from fv3config.config.diag_table import (
    DiagTable,
    DiagFieldConfig,
    DiagFileConfig,
)
from fv3config._exceptions import ConfigError


def diag_field():
    return DiagFieldConfig("dynamics", "u850", "zonal_wind_at_850hPa")


def diag_file(name):
    return DiagFileConfig(name, 1, "hours", [diag_field(), diag_field()])


@pytest.fixture
def diag_table():
    return DiagTable(
        "experiment",
        datetime(2000, 1, 1),
        [diag_file("first_diagnostics"), diag_file("second_diagnostics")],
    )


def test_DiagTable_string_round_trip(diag_table):
    round_tripped_diag_table = DiagTable.from_str(str(diag_table))
    assert str(diag_table) == str(round_tripped_diag_table)


def test_DiagTable_dict_round_trip(diag_table):
    round_tripped_diag_table = DiagTable.from_dict(diag_table.asdict())
    assert str(diag_table) == str(round_tripped_diag_table)


def test_DiagTable__repr__(diag_table):
    expected_str = """experiment
2000 1 1 0 0 0

"first_diagnostics", 1, "hours", 1, "hours", "time"
"second_diagnostics", 1, "hours", 1, "hours", "time"

"dynamics", "u850", "zonal_wind_at_850hPa", "first_diagnostics", "all", "none", "none", 2
"dynamics", "u850", "zonal_wind_at_850hPa", "first_diagnostics", "all", "none", "none", 2

"dynamics", "u850", "zonal_wind_at_850hPa", "second_diagnostics", "all", "none", "none", 2
"dynamics", "u850", "zonal_wind_at_850hPa", "second_diagnostics", "all", "none", "none", 2
"""
    assert str(diag_table) == expected_str


def test_DiagTable_as_dict(diag_table):
    expected_dict = {
        "name": "experiment",
        "base_time": datetime(2000, 1, 1, 0, 0),
        "file_configs": [
            {
                "name": "first_diagnostics",
                "frequency": 1,
                "frequency_units": "hours",
                "field_configs": [
                    {
                        "module_name": "dynamics",
                        "field_name": "u850",
                        "output_name": "zonal_wind_at_850hPa",
                        "reduction_method": "none",
                        "time_sampling": "all",
                        "regional_section": "none",
                        "packing": 2,
                    },
                    {
                        "module_name": "dynamics",
                        "field_name": "u850",
                        "output_name": "zonal_wind_at_850hPa",
                        "reduction_method": "none",
                        "time_sampling": "all",
                        "regional_section": "none",
                        "packing": 2,
                    },
                ],
                "file_format": 1,
                "time_axis_units": "hours",
                "time_axis_name": "time",
            },
            {
                "name": "second_diagnostics",
                "frequency": 1,
                "frequency_units": "hours",
                "field_configs": [
                    {
                        "module_name": "dynamics",
                        "field_name": "u850",
                        "output_name": "zonal_wind_at_850hPa",
                        "reduction_method": "none",
                        "time_sampling": "all",
                        "regional_section": "none",
                        "packing": 2,
                    },
                    {
                        "module_name": "dynamics",
                        "field_name": "u850",
                        "output_name": "zonal_wind_at_850hPa",
                        "reduction_method": "none",
                        "time_sampling": "all",
                        "regional_section": "none",
                        "packing": 2,
                    },
                ],
                "file_format": 1,
                "time_axis_units": "hours",
                "time_axis_name": "time",
            },
        ],
    }
    assert expected_dict == diag_table.asdict()


def test_from_str():
    input_str = """default_experiment
2016 08 01 00 0 0
#output files
"atmos_static",           -1,  "hours",    1, "hours", "time",
"atmos_dt_atmos",          2,  "hours",    1, "hours",  "time" #inline comment
"empty_file",              2,  "hours",    1, "hours",  "time"
#
 #output variables
#

###
# atmos_static
###
  "dynamics",      "zsurf",       "HGTsfc",       "atmos_static",      "all", .false.,  "none", 2
###
# atmos_dt_atmos
###
"dynamics",  "us",          "UGRDlowest",    "atmos_dt_atmos", "all", .false.,  "none", 2, # inline comment
"dynamics",  "u850",        "UGRD850",       "atmos_dt_atmos", "all", .true.,  "none", 2
"""

    diag_table = DiagTable.from_str(input_str)
    assert diag_table.name == "default_experiment"
    assert diag_table.base_time == datetime(2016, 8, 1)
    assert len(diag_table.file_configs) == 3
    assert diag_table.file_configs[0] == DiagFileConfig(
        "atmos_static", -1, "hours", [DiagFieldConfig("dynamics", "zsurf", "HGTsfc")],
    )
    assert diag_table.file_configs[1] == DiagFileConfig(
        "atmos_dt_atmos",
        2,
        "hours",
        [
            DiagFieldConfig("dynamics", "us", "UGRDlowest"),
            DiagFieldConfig("dynamics", "u850", "UGRD850", reduction_method="average"),
        ],
    )


@pytest.mark.parametrize(
    "diag_table_str",
    [
        """default_experiment
2016 08 01 00 0 0
"dynamics", "zsurf", "HGTsfc", "atmos_static", "all", .false.,  "none", 2
"atmos_static", -1,  "hours", 1, "hours", "time"
""",
        """default experiment
2016 08 01 00 0 0
"atmos_static", -1,  "hours", 1, "hours", "time"
"dynamics", "zsurf", "HGTsfc", "atmos_static", "all", .false.,  "none", 2
""",
    ],
    ids=["field_defined_before_corresponding_file", "spaces_in_name"],
)
def test_from_str_raises_config_error(diag_table_str):
    with pytest.raises(ConfigError):
        DiagTable.from_str(diag_table_str)


@pytest.mark.parametrize(
    "input_,expected_output",
    [
        ('"name"', "name"),
        (".true.", "average"),
        (".TRUE.", "average"),
        (".false.", "none"),
        (".FALSE.", "none"),
        ("3", 3),
    ],
)
def test__str_to_token(input_, expected_output):
    output = DiagTable._str_to_token(input_)
    assert output == expected_output


@pytest.mark.parametrize(
    "token,expected_output", [("name", '"name"'), (3, "3")],
)
def test__token_to_str(token, expected_output):
    output = DiagTable._token_to_str(token)
    assert output == expected_output
