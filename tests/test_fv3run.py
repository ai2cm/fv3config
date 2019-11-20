import unittest
import os
import shutil
import tempfile
import pytest
import yaml
import subprocess
import fv3config

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
MOCK_RUNSCRIPT = os.path.abspath(os.path.join(TEST_DIR, 'testdata/mock_runscript.py'))
DOCKER_IMAGE_NAME = 'us.gcr.io/vcm-ml/fv3gfs-python'


def subprocess_run(config_dict, outdir):
    with tempfile.NamedTemporaryFile(mode='w') as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.flush()
        subprocess.check_call(
            ['fv3run', config_file.name, outdir, '--runfile', MOCK_RUNSCRIPT]
        )


def docker_run(config_dict, outdir):
    with tempfile.NamedTemporaryFile(mode='w') as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.flush()
        subprocess.check_call(
            ['fv3run', config_file.name, outdir, '--runfile', MOCK_RUNSCRIPT,
             '--dockerimage', DOCKER_IMAGE_NAME]
        )


def config_dict_module_run(config_dict, outdir):
    fv3config.run(config_dict, outdir, runfile=MOCK_RUNSCRIPT)


def config_dict_filename_run(config_dict, outdir):
    with tempfile.NamedTemporaryFile(mode='w') as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.flush()
        fv3config.run(config_file.name, outdir, runfile=MOCK_RUNSCRIPT)


def count_executed_ranks(rundir):
    filenames = os.listdir(rundir)
    total = 0
    while f'rank_{total}' in filenames:
        total += 1
    return total


@pytest.mark.parametrize(
    "runner",
    [subprocess_run, docker_run, config_dict_module_run, config_dict_filename_run]
)
def test_fv3run(runner):
    fv3config.ensure_data_is_downloaded()
    outdir = os.path.join(TEST_DIR, 'outdir')
    try:
        runner(fv3config.get_default_config(), outdir)
        assert count_executed_ranks(outdir) == 6
    finally:
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
