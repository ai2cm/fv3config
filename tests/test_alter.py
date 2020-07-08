import fv3config
import pytest
from datetime import timedelta


@pytest.fixture
def config(c12_config):
    return c12_config


@pytest.fixture(params=["seconds", "hours", "days", "years"])
def new_duration(request):
    if request.param == "seconds":
        return timedelta(seconds=5)
    elif request.param == "hours":
        return timedelta(hours=5)
    elif request.param == "days":
        return timedelta(days=7)
    elif request.param == "years":
        return timedelta(days=365 * 10)


def test_set_run_duration_sets_duration(config, new_duration):
    new_config = fv3config.set_run_duration(config, new_duration)
    assert fv3config.get_run_duration(new_config) == new_duration


def test_set_run_duration_returns_new_dict(config, new_duration):
    new_config = fv3config.set_run_duration(config, new_duration)
    assert new_config is not config
    assert new_config["namelist"] is not config["namelist"]


def test_set_run_duration_invalid_config(config, new_duration):
    config.pop("namelist")
    with pytest.raises(fv3config.ConfigError):
        fv3config.set_run_duration(config, new_duration)
