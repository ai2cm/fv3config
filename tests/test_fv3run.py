import unittest
import os
import shutil
import tempfile
import contextlib
import collections
import subprocess
from subprocess import check_call as original_check_call
import pytest
import yaml
import fv3config

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
MOCK_RUNSCRIPT = os.path.abspath(os.path.join(TEST_DIR, 'testdata/mock_runscript.py'))
DOCKER_IMAGE_NAME = 'us.gcr.io/vcm-ml/fv3gfs-python'
USER_UID_GID = f'{os.getuid()}:{os.getgid()}'

MockTempfile = collections.namedtuple('MockTempfile', ['name'])

MPI_ENABLED = (shutil.which('mpirun') is not None)
DOCKER_ENABLED = (shutil.which('docker') is not None)


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


@contextlib.contextmanager
def mocked_check_call():
    call_list = []

    def mock_check_call(arg_list, *args, **kwargs):
        call_list.append(arg_list)
        if arg_list[0] == 'mpirun':
            pass
        else:
            original_check_call(arg_list, *args, **kwargs)
    subprocess.check_call = mock_check_call
    try:
        yield call_list
    finally:
        subprocess.check_call = original_check_call


@contextlib.contextmanager
def cleaned_up_directory(dirname):
    try:
        yield
    finally:
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)


@pytest.mark.parametrize(
    "runner",
    [subprocess_run, docker_run, config_dict_module_run, config_dict_filename_run]
)
def test_fv3run_without_mpi(runner):
    # the test for docker_run *will* use MPI inside the docker container
    # we're only making it so subprocess calls of mpirun don't execute
    if runner == docker_run and not DOCKER_ENABLED:
        pytest.skip('docker is not enabled')
    fv3config.ensure_data_is_downloaded()
    outdir = os.path.join(TEST_DIR, 'outdir')
    with mocked_check_call(), cleaned_up_directory(outdir):
        runner(fv3config.get_default_config(), outdir)


@pytest.mark.skipif(not MPI_ENABLED, reason='mpirun must be available')
@pytest.mark.parametrize(
    "runner",
    [subprocess_run, config_dict_module_run, config_dict_filename_run]
)
def test_fv3run_with_mpi(runner):
    # docker_run does not need MPI outside the docker container to test, so it's
    # tested in the "without_mpi" tests.
    fv3config.ensure_data_is_downloaded()
    outdir = os.path.join(TEST_DIR, 'outdir')
    with cleaned_up_directory(outdir):
        runner(fv3config.get_default_config(), outdir)
        assert count_executed_ranks(outdir) == 6


@pytest.mark.parametrize(
    "runfile, expected_bind_mount_args, expected_python_args",
    [
        [
            '/tmp/runfile.py',
            ['-v', '/tmp/runfile.py:/runfile.py'],
            ['--runfile', '/runfile.py']
        ],
        [
            'relative.py',
            ['-v', f"{os.path.join(os.getcwd(), 'relative.py')}:/runfile.py"],
            ['--runfile', '/runfile.py']
        ],
        [
            'gs://bucket-name/runfile.py',
            [],
            ['--runfile', 'gs://bucket-name/runfile.py']
        ],
    ])
def test_get_runfile_args(runfile, expected_bind_mount_args, expected_python_args):
    bind_mount_args = []
    python_args = []
    fv3config.fv3run._run._get_runfile_args(runfile, bind_mount_args, python_args)
    assert bind_mount_args == expected_bind_mount_args
    assert python_args == expected_python_args


@pytest.mark.parametrize(
    "config, tempfile, expected_config_location, expected_bind_mount_args",
    [
        [
            fv3config.get_default_config(),
            MockTempfile(name='/tmp/file'),
            fv3config.fv3run._run.DOCKER_CONFIG_LOCATION,
            ['-v', '/tmp/file:/fv3config.yaml']
        ],
        [
            '/absolute/path/fv3config.yaml',
            MockTempfile(name='/tmp/file'),
            fv3config.fv3run._run.DOCKER_CONFIG_LOCATION,
            ['-v', '/absolute/path/fv3config.yaml:/fv3config.yaml']
        ],
        [
            'gs://bucket-name/fv3config.yaml',
            MockTempfile(name='/tmp/file'),
            'gs://bucket-name/fv3config.yaml',
            []
        ]
    ])
def test_get_config_args(
        config, tempfile, expected_config_location, expected_bind_mount_args):
    bind_mount_args = []
    config_location = fv3config.fv3run._run._get_config_args(
        config, tempfile, bind_mount_args)
    assert config_location == expected_config_location
    assert bind_mount_args == expected_bind_mount_args


@pytest.mark.parametrize(
    "outdir, expected_docker_args, expected_bind_mount_args",
    [
        [
            'relative/',
            ['--user', USER_UID_GID],
            ['-v', f"{os.path.join(os.getcwd(), 'relative')}:/outdir"],
        ],
        [
            '/abs/path/',
            ['--user', USER_UID_GID],
            ['-v', f"/abs/path:/outdir"],
        ],
    ])
def test_get_docker_args(
        outdir, expected_docker_args, expected_bind_mount_args):
    docker_args = []
    bind_mount_args = []
    fv3config.fv3run._run._get_docker_args(
        docker_args, bind_mount_args, outdir)
    assert docker_args == expected_docker_args
    assert bind_mount_args == expected_bind_mount_args


@pytest.mark.parametrize(
    "keyfile, expected_docker_args, expected_bind_mount_args",
    [
        [
            None,
            [],
            [],
        ],
        [
            'relative_key.json',
            ['-e', 'GOOGLE_APPLICATION_CREDENTIALS=/gcs_key.json'],
            ['-v', f"{os.path.join(os.getcwd(), 'relative_key.json')}:/gcs_key.json"],
        ],
        [
            '/abs/key.json',
            ['-e', 'GOOGLE_APPLICATION_CREDENTIALS=/gcs_key.json'],
            ['-v', '/abs/key.json:/gcs_key.json'],
        ]
    ])
def test_get_credentials_args(
        keyfile, expected_docker_args, expected_bind_mount_args):
    docker_args = []
    bind_mount_args = []
    fv3config.fv3run._run._get_credentials_args(
        keyfile, docker_args, bind_mount_args)
    assert docker_args == expected_docker_args
    assert bind_mount_args == expected_bind_mount_args
