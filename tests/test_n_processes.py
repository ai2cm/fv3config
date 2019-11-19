import fv3config
import pytest


@pytest.mark.parametrize(
    "ntiles,layout,expected",
    [
        (6, (1, 1), 6),
        (6, (2, 2), 24),
        (6, (2, 3), 36),
        (1, (3, 3), 9),
    ]
)
def test_get_n_processes(ntiles, layout, expected):
    config_dict = {
        'namelist': {
            'fv_core_nml': {
                'ntiles': ntiles,
                'layout': layout,
            }
        }
    }
    result = fv3config.get_n_processes(config_dict)
    assert result == expected
