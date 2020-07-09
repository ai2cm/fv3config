import fv3config
import pytest
from datetime import timedelta


@pytest.fixture
def config(c12_config):
    return c12_config


@pytest.mark.parametrize(
    "coupler_nml, duration",
    [
        ({"seconds": 10}, timedelta(seconds=10)),
        ({"minutes": 2}, timedelta(minutes=2)),
        ({"hours": 100}, timedelta(hours=100)),
        ({"days": 9}, timedelta(days=9)),
        ({"months": 6}, None),
        ({"seconds": 5, "minutes": 1, "hours": 1}, timedelta(seconds=65, hours=1)),
    ],
)
def test_get_run_duration(coupler_nml, duration, config):
    config["namelist"]["coupler_nml"] = coupler_nml
    if coupler_nml.get("months", 0) != 0:
        with pytest.raises(ValueError):
            fv3config.get_run_duration(config)
    else:
        assert fv3config.get_run_duration(config) == duration
