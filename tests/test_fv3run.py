import unittest
import unittest.mock
import os
import shutil
import tempfile
import contextlib
import collections
import subprocess
import pytest
import yaml
import fv3config

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
            ["fv3run", config_file.name, outdir, "--runfile", MOCK_RUNSCRIPT]
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


@pytest.mark.parametrize("runner", [config_dict_module_run, config_dict_filename_run])
def test_fv3run_with_mocked_subprocess(runner):
    fv3config.ensure_data_is_downloaded()
    outdir = os.path.join(TEST_DIR, "outdir")

    with unittest.mock.patch("subprocess.check_call") as mock, cleaned_up_directory(
        outdir
    ):
        runner(fv3config.get_default_config(), outdir)
        assert mock.called
        assert mock.call_args[0] == (
            [
                "mpirun",
                "-n",
                "6",
                "--allow-run-as-root",
                "--use-hwthread-cpus",
                "python3",
                "-m",
                "mpi4py",
                "mock_runscript.py",
            ],
        )
        config = yaml.safe_load(open(os.path.join(outdir, "fv3config.yml"), "r"))
        assert config == fv3config.get_default_config()


@pytest.mark.skipif(
    not DOCKER_ENABLED,
    reason=f"docker or docker image {DOCKER_IMAGE_NAME} is not available",
)
def test_fv3run_docker():
    """End-to-end test of running a mock runscript inside a docker container.
    """
    outdir = os.path.join(TEST_DIR, "outdir")

    with cleaned_up_directory(outdir):
        fv3config.run_docker(
            fv3config.get_default_config(),
            outdir,
            DOCKER_IMAGE_NAME,
            runfile=MOCK_RUNSCRIPT,
        )
        check_run_directory(outdir)


@pytest.mark.skipif(not MPI_ENABLED, reason="mpirun must be available")
@pytest.mark.parametrize(
    "runner", [subprocess_run, config_dict_module_run, config_dict_filename_run]
)
def test_fv3run_with_mpi(runner):
    fv3config.ensure_data_is_downloaded()
    outdir = os.path.join(TEST_DIR, "outdir")
    with cleaned_up_directory(outdir):
        runner(fv3config.get_default_config(), outdir)
        check_run_directory(outdir)


@pytest.mark.parametrize(
    "runfile, expected_bind_mount_args, expected_python_args",
    [
        [
            "/tmp/runfile.py",
            ["-v", "/tmp/runfile.py:/runfile.py"],
            ["--runfile", "/runfile.py"],
        ],
        [
            "relative.py",
            ["-v", f"{os.path.join(os.getcwd(), 'relative.py')}:/runfile.py"],
            ["--runfile", "/runfile.py"],
        ],
        [
            "gs://bucket-name/runfile.py",
            [],
            ["--runfile", "gs://bucket-name/runfile.py"],
        ],
    ],
)
def test_get_runfile_args(runfile, expected_bind_mount_args, expected_python_args):
    bind_mount_args = []
    python_args = []
    fv3config.fv3run._docker._get_runfile_args(runfile, bind_mount_args, python_args)
    assert bind_mount_args == expected_bind_mount_args
    assert python_args == expected_python_args


@pytest.mark.parametrize(
    "config, tempfile, expected_config_location, expected_bind_mount_args",
    [
        [
            fv3config.get_default_config(),
            MockTempfile(name="/tmp/file"),
            fv3config.fv3run._docker.DOCKER_CONFIG_LOCATION,
            ["-v", "/tmp/file:/fv3config.yml"],
        ],
        [
            "/absolute/path/fv3config.yml",
            MockTempfile(name="/tmp/file"),
            fv3config.fv3run._docker.DOCKER_CONFIG_LOCATION,
            ["-v", "/absolute/path/fv3config.yml:/fv3config.yml"],
        ],
        [
            "gs://bucket-name/fv3config.yml",
            MockTempfile(name="/tmp/file"),
            "gs://bucket-name/fv3config.yml",
            [],
        ],
    ],
)
def test_get_config_args(
    config, tempfile, expected_config_location, expected_bind_mount_args
):
    bind_mount_args = []
    config_location = fv3config.fv3run._docker._get_config_args(
        config, tempfile, bind_mount_args
    )
    assert config_location == expected_config_location
    assert bind_mount_args == expected_bind_mount_args


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
