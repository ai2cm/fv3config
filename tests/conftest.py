import pytest
import os
import yaml

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def c12_config():
    with open(os.path.join(TEST_DIR, "c12_config.yml"), "r") as f:
        return yaml.safe_load(f)
