import collections
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

import gcsfs
import pytest
import yaml

import fv3config
from fv3config.fv3run._native import (
    RUNFILE_ENV_VAR,
    _output_stream_context,
    _get_python_command,
    call_via_subprocess,
)

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
MOCK_RUNSCRIPT = os.path.abspath(os.path.join(TEST_DIR, "testdata/mock_runscript.py"))
DOCKER_IMAGE_NAME = "us.gcr.io/vcm-ml/fv3gfs-python"
USER_UID_GID = f"{os.getuid()}:{os.getgid()}"

MockTempfile = collections.namedtuple("MockTempfile", ["name"])

MPI_ENABLED = shutil.which("mpirun") is not None
try:

    subprocess.check_call(
        ["docker", "image", "inspect", DOCKER_IMAGE_NAME],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    DOCKER_ENABLED = True
except (subprocess.CalledProcessError, FileNotFoundError):
    DOCKER_ENABLED = False


def subprocess_run(config_dict, outdir):
    with tempfile.NamedTemporaryFile(mode="w") as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.flush()
        subprocess.check_call(
            [
                "fv3run",
                config_file.name,
                outdir,
                "--runfile",
                MOCK_RUNSCRIPT,
                "--capture-output",
            ]
        )


def docker_run(config_dict, outdir):
    with tempfile.NamedTemporaryFile(mode="w") as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.flush()
        try:
            subprocess.check_call(
                [
                    "fv3run",
                    config_file.name,
                    outdir,
                    "--runfile",
                    MOCK_RUNSCRIPT,
                    "--dockerimage",
                    DOCKER_IMAGE_NAME,
                ]
            )
        except subprocess.CalledProcessError as err:
            if os.path.isfile(os.path.join(outdir, "stdout.log")):
                with open(os.path.join(outdir, "stdout.log")) as stdout:
                    print(f"STDOUT: {stdout.read()}")
            if os.path.isfile(os.path.join(outdir, "stderr.log")):
                with open(os.path.join(outdir, "stderr.log")) as stderr:
                    print(f"STDERR: {stderr.read()}")
            raise err


def config_dict_module_run(config_dict, outdir):
    fv3config.run_native(config_dict, outdir, runfile=MOCK_RUNSCRIPT)


def config_dict_filename_run(config_dict, outdir):
    with tempfile.NamedTemporaryFile(mode="w") as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.flush()
        fv3config.run_native(config_file.name, outdir, runfile=MOCK_RUNSCRIPT)


def count_executed_ranks(rundir):
    filenames = os.listdir(rundir)
    total = 0
    while f"rank_{total}" in filenames:
        total += 1
    return total


@pytest.fixture
def config(c12_config):
    return c12_config


@contextlib.contextmanager
def cleaned_up_directory(dirname):
    try:
        yield
    finally:
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)


def check_run_directory(dirname):
    filenames = os.listdir(dirname)
    assert "stdout.log" in filenames
    assert "stderr.log" in filenames
    assert count_executed_ranks(dirname) == 6
    assert "input.nml" in filenames
    assert "INPUT" in filenames


@pytest.mark.filterwarnings("ignore:could not remove stacksize limit")
@pytest.mark.parametrize("runner", [config_dict_module_run, config_dict_filename_run])
def test_fv3run_with_mocked_subprocess(runner, config):
    outdir = os.path.join(TEST_DIR, "outdir")

    with unittest.mock.patch("subprocess.check_call") as mock, cleaned_up_directory(
        outdir
    ):
        runner(config, outdir)
        assert mock.called
        call_args = list(mock.call_args[0])
        # ensure test does not depend on # of processors on testing system
        while "--oversubscribe" in call_args[0]:
            call_args[0].remove("--oversubscribe")
        assert call_args == [
            [
                "mpirun",
                "-n",
                "6",
                "--allow-run-as-root",
                "--use-hwthread-cpus",
                "--mca",
                "btl_vader_single_copy_mechanism",
                "none",
                "python3",
                "-m",
                "mpi4py",
                "mock_runscript.py",
            ]
        ]
        written_config = yaml.safe_load(
            open(os.path.join(outdir, "fv3config.yml"), "r")
        )
        assert written_config == config


@pytest.mark.parametrize(
    "runfile, expected_bind_mount_args, expected_python_args",
    [
        ["/tmp/runfile.py", ["-v", "/tmp/runfile.py:/runfile.py"], "/runfile.py"],
        [
            "relative.py",
            ["-v", f"{os.path.join(os.getcwd(), 'relative.py')}:/runfile.py"],
            "/runfile.py",
        ],
        ["gs://bucket-name/runfile.py", [], "gs://bucket-name/runfile.py"],
    ],
)
def test_get_runfile_args(runfile, expected_bind_mount_args, expected_python_args):
    bind_mount_args = []
    runfile = fv3config.fv3run._docker._get_runfile_args(runfile, bind_mount_args)
    assert bind_mount_args == expected_bind_mount_args


@pytest.mark.parametrize(
    "runfile, env_var, expected",
    [
        ("/path/to/runfile.py", None, ["python3", "-m", "mpi4py", "runfile.py"]),
        ("a", "b", ["python3", "-m", "mpi4py", "a"]),
        (
            None,
            "/path/to/runfile.py",
            ["python3", "-m", "mpi4py", "/path/to/runfile.py"],
        ),
        (None, None, ["python3", "-m", "mpi4py", "-m", "fv3gfs.run"]),
    ],
)
def test__get_native_python_args(monkeypatch, runfile, expected, env_var):
    if env_var is not None:
        monkeypatch.setenv(RUNFILE_ENV_VAR, env_var)
    assert _get_python_command(runfile) == expected


_original_get_file = fv3config.filesystem.get_file


def test__output_stream_context_captured(tmpdir):
    err_msg = b"error"
    out_msg = b"output"
    with _output_stream_context(tmpdir, True) as (stdout, stderr):
        stdout.write(out_msg)
        stderr.write(err_msg)

    with open(tmpdir.join("stderr.log"), "rb") as f:
        assert err_msg == f.read()

    with open(tmpdir.join("stdout.log"), "rb") as f:
        assert out_msg == f.read()


def test__output_stream_context_uncaptured(tmpdir):
    with _output_stream_context(tmpdir, False) as (stdout, stderr):
        assert stdout == sys.stdout
        assert stderr == sys.stderr


def maybe_get_file(*args, **kwargs):
    try:
        _original_get_file(*args, **kwargs)
    except (OSError, gcsfs.utils.HttpError):
        pass


@pytest.mark.parametrize(
    "outdir, expected_docker_args, expected_bind_mount_args",
    [
        [
            "relative/",
            ["--rm", "--user", USER_UID_GID],
            ["-v", f"{os.path.join(os.getcwd(), 'relative')}:/outdir"],
        ],
        ["/abs/path/", ["--rm", "--user", USER_UID_GID], ["-v", f"/abs/path:/outdir"]],
    ],
)
def test_get_docker_args(outdir, expected_docker_args, expected_bind_mount_args):
    docker_args = []
    bind_mount_args = []
    fv3config.fv3run._docker._get_docker_args(docker_args, bind_mount_args, outdir)
    assert docker_args == expected_docker_args
    assert bind_mount_args == expected_bind_mount_args


@pytest.mark.parametrize(
    "keyfile, expected_docker_args, expected_bind_mount_args",
    [
        [None, [], []],
        [
            "relative_key.json",
            ["-e", "GOOGLE_APPLICATION_CREDENTIALS=/gcs_key.json"],
            ["-v", f"{os.path.join(os.getcwd(), 'relative_key.json')}:/gcs_key.json"],
        ],
        [
            "/abs/key.json",
            ["-e", "GOOGLE_APPLICATION_CREDENTIALS=/gcs_key.json"],
            ["-v", "/abs/key.json:/gcs_key.json"],
        ],
    ],
)
def test_get_credentials_args(keyfile, expected_docker_args, expected_bind_mount_args):
    docker_args = []
    bind_mount_args = []
    fv3config.fv3run._docker._get_credentials_args(
        keyfile, docker_args, bind_mount_args
    )
    assert docker_args == expected_docker_args
    assert bind_mount_args == expected_bind_mount_args


@pytest.mark.parametrize(
    "config_dict, local_paths",
    [
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "default",
                "forcing": "gs://bucket/forcing/default",
                "diag_table": "gs://bucket/diag/default",
                "data_table": "gs://bucket/data_table/default",
            },
            [],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "/local/initial/conditions",
                "forcing": "gs://bucket/forcing/default",
                "diag_table": "gs://bucket/diag/default",
                "data_table": "gs://bucket/data_table/default",
            },
            ["/local/initial/conditions"],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "/local/initial/conditions",
                "forcing": "/local/forcing/default",
                "diag_table": "/local/diag/default",
                "data_table": "gs://bucket/data_table/default",
            },
            [
                "/local/initial/conditions",
                "/local/forcing/default",
                "/local/diag/default",
            ],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "gs://bucket/initial_conditions/default",
                "forcing": [
                    {
                        "source_location": "/local/directory",
                        "source_name": "source_name.nc",
                        "target_location": "INPUT/",
                        "target_name": "filename.nc",
                        "copy_method": "copy",
                    }
                ],
                "diag_table": "/local/diag/default",
                "data_table": "gs://bucket/data_table/default",
            },
            ["/local/directory/source_name.nc", "/local/diag/default"],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "gs://bucket/initial_conditions/default",
                "forcing": "gs://bucket/forcing/default",
                "diag_table": [
                    {
                        "source_location": "gs://remote/directory",
                        "source_name": "source_name.nc",
                        "target_location": "INPUT/",
                        "target_name": "filename.nc",
                        "copy_method": "copy",
                    }
                ],
                "data_table": "gs://bucket/data_table/default",
            },
            [],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "gs://bucket/initial_conditions/default",
                "forcing": "gs://bucket/forcing/default",
                "diag_table": [
                    {
                        "source_location": "gs://remote/directory",
                        "source_name": "source_name.nc",
                        "target_location": "INPUT/",
                        "target_name": "filename.nc",
                        "copy_method": "copy",
                    }
                ],
                "data_table": "gs://bucket/data_table/default",
                "patch_files": [],
            },
            [],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "gs://bucket/initial_conditions/default",
                "forcing": "gs://bucket/forcing/default",
                "diag_table": [
                    {
                        "source_location": "gs://remote/directory",
                        "source_name": "source_name.nc",
                        "target_location": "INPUT/",
                        "target_name": "filename.nc",
                        "copy_method": "copy",
                    }
                ],
                "data_table": "gs://bucket/data_table/default",
                "patch_files": {
                    "source_location": "gs://remote/directory",
                    "source_name": "source_name.nc",
                    "target_location": "INPUT/",
                    "target_name": "filename.nc",
                    "copy_method": "copy",
                },
            },
            [],
        ],
        [
            {
                "experiment_name": "default_experiment",
                "initial_conditions": "gs://bucket/initial_conditions/default",
                "forcing": "gs://bucket/forcing/default",
                "diag_table": [
                    {
                        "source_location": "gs://remote/directory",
                        "source_name": "source_name.nc",
                        "target_location": "INPUT/",
                        "target_name": "filename.nc",
                        "copy_method": "copy",
                    }
                ],
                "data_table": "gs://bucket/data_table/default",
                "patch_files": [
                    {
                        "source_location": "/local/directory",
                        "source_name": "source_name.nc",
                        "target_location": "INPUT/",
                        "target_name": "filename.nc",
                        "copy_method": "copy",
                    }
                ],
            },
            ["/local/directory/source_name.nc"],
        ],
    ],
)
def test_get_local_paths(config_dict, local_paths):
    return_value = fv3config.fv3run._docker._get_local_data_paths(config_dict)
    assert set(return_value) == set(local_paths)  # order does not matter


def test_call_via_subprocess_command():
    import json

    @call_via_subprocess(__name__)
    def dummy_function(*obj, **kwargs):
        pass

    command = dummy_function.command(1, a=1, b=1)
    args = command.pop()
    assert json.loads(args) == [[1], dict(a=1, b=1)]
    assert command == ["python", "-m", dummy_function.__module__]


def test_call_via_subprocess_main():

    # need to append outputs here since call_via_subprocess does not
    # support return arguments
    output = []

    @call_via_subprocess(__name__)
    def dummy_function(*obj):
        output.append(hash(obj))

    inputs = (1, 2, 3)

    # first call is via "main"
    serialized_args = dummy_function.command(*inputs)[-1]
    argv = [None, serialized_args]
    dummy_function.main(argv)
    dummy_ans = output.pop()

    # second call is normal python call
    dummy_function(*inputs)
    python_ans = output.pop()

    # assert results where the same
    assert dummy_ans == python_ans


def test_call_via_subprocess_command_fails_with_bad_args():
    @call_via_subprocess(__name__)
    def dummy_function(a, b):
        pass

    with pytest.raises(TypeError):
        dummy_function.command(1, 2, 3, king="kong")
