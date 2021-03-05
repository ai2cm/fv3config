import fv3config
import io
import datetime
import pytest
from toolz import assoc, dissoc

diag_table_obj = fv3config.DiagTable(
    name="example_diag_table",
    base_time=datetime.datetime(2000, 1, 1),
    file_configs=[
        fv3config.DiagFileConfig(
            name="physics_diagnostics",
            frequency=1,
            frequency_units="hours",
            field_configs=[
                fv3config.DiagFieldConfig(
                    "gfs_phys", "totprcb_ave", "surface_precipitation_rate"
                ),
                fv3config.DiagFieldConfig(
                    "gfs_phys", "ULWRFtoa", "upward_longwave_radiative_flux_at_toa"
                ),
            ],
        )
    ],
)


@pytest.mark.parametrize("diag_table", [diag_table_obj, "default"])
def test_dump_load(c12_config, diag_table):
    f = io.StringIO()
    config = assoc(c12_config, "diag_table", diag_table)
    fv3config.dump(config, f)
    f.seek(0)
    loaded = fv3config.load(f)

    if isinstance(config["diag_table"], fv3config.DiagTable):
        assert config == loaded
    else:
        assert dissoc(config, "diag_table") == dissoc(loaded, "diag_table")
