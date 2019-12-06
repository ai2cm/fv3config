from collections import namedtuple
import pytest
import fv3config

MemoryArgs = namedtuple(
    'MemoryArgs', ['memory_gb', 'memory_gb_limit_in', 'memory_gb_limit']
)


@pytest.fixture
def config_location():
    return 'gs://my-bucket/fv3config.yml'


@pytest.fixture
def outdir():
    return 'gs://my-bucket/rundir'


@pytest.fixture(params=['default', 'tagged'])
def docker_image(request):
    if request.param == 'default':
        return 'us.gcr.io/vcm-ml/fv3gfs-python'
    elif request.param == 'tagged':
        return 'us.gcr.io/vcm-ml/fv3gfs-python:1.0'


@pytest.fixture(params=['gcloud', 'local'])
def runfile(request):
    if request.param == 'gcloud':
        return 'gs://my-bucket/runfile.py'
    if request.param == 'local':
        return '/inside/docker/dir/runfile.py'


@pytest.fixture
def jobname():
    return 'my-job-name'


@pytest.fixture(params=["default", "manual_limit"])
def memory_args(request):
    return {
        "default": MemoryArgs(3.6, None, 3.6),
        "manual_limit": MemoryArgs(3.6, 4.0, 4.0),
    }[request.param]


@pytest.fixture(params=["1_cpu", "2.5_cpu"])
def cpu_count(request):
    if request.param == "1_cpu":
        return 1
    elif request.param == "2.5_cpu":
        return 2.5


@pytest.fixture(params=['my-secret-name', None])
def gcp_secret(request):
    return request.param


@pytest.fixture(
    params=['Always', 'IfNotPresent']
)
def image_pull_policy(request):
    return request.param


def test_local_config_rejected(outdir, docker_image, runfile):
    with pytest.raises(ValueError):
        fv3config.fv3run._kubernetes._get_job(
            '/local/dir/config.yml', outdir, docker_image, runfile)


def test_local_outdir_rejected(config_location, docker_image, runfile):
    with pytest.raises(ValueError):
        fv3config.fv3run._kubernetes._get_job(
            config_location, '/local/outdir', docker_image, runfile)


def test_get_job(
        config_location, outdir, docker_image, runfile, jobname,
        memory_args, cpu_count, gcp_secret, image_pull_policy):
    job = fv3config.fv3run._kubernetes._get_job(
        config_location, outdir, docker_image, runfile, jobname,
        memory_args.memory_gb, memory_args.memory_gb_limit_in,
        cpu_count, gcp_secret, image_pull_policy)
    _check_job(job, jobname)
    job_spec = job.spec
    _check_job_spec(job_spec)
    pod_spec = job_spec.template.spec
    assert pod_spec.restart_policy == 'Never'
    container = pod_spec.containers[0]
    _check_command(container.command, outdir, config_location, runfile)
    assert container.image == docker_image
    assert container.image_pull_policy == image_pull_policy
    _check_secret_mount(gcp_secret, container, pod_spec)
    if gcp_secret is not None:
        _check_env(container.env, 'GOOGLE_APPLICATION_CREDENTIALS', '/secret/gcp-credentials/key.json')
        _check_env(container.env, 'CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE', '/secret/gcp-credentials/key.json')
    else:
        _check_env(container.env, 'GOOGLE_APPLICATION_CREDENTIALS', None)
        _check_env(container.env, 'CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE', None)
    _check_resource_requirements(
        container, memory_args.memory_gb, memory_args.memory_gb_limit, cpu_count)


def _check_job(job, jobname):
    assert job.kind == 'Job'
    assert job.api_version == 'batch/v1'
    assert hasattr(job.metadata, 'name')
    if jobname is not None:
        assert job.metadata.name == jobname


def _check_job_spec(job_spec):
    assert job_spec.backoff_limit == 0
    assert job_spec.completions == 1
    assert job_spec.ttl_seconds_after_finished == 100


def _check_command(command, outdir, config_location, runfile):
    assert outdir in command
    assert config_location in command
    assert runfile in command
    assert command[command.index(runfile) - 1] == '--runfile'


def _check_secret_mount(gcp_secret, container, pod_spec):
    if gcp_secret is None:
        assert len(pod_spec.volumes) == 0
        assert len(container.volume_mounts) == 0
    else:
        assert len(pod_spec.volumes) == 1
        assert pod_spec.volumes[0].secret.secret_name == gcp_secret
        assert len(container.volume_mounts) == 1
        assert container.volume_mounts[0].name == pod_spec.volumes[0].name
        assert container.volume_mounts[0].read_only
        assert container.volume_mounts[0].mount_path == '/secret/gcp-credentials'


def _check_resource_requirements(container, memory_gb, memory_gb_limit, cpu_count):
    resource_reqs = container.resources
    assert resource_reqs.limits['memory'] == f'{memory_gb_limit:.1f}G'
    assert resource_reqs.requests['memory'] == f'{memory_gb:.1f}G'
    assert resource_reqs.requests['cpu'] == f'{cpu_count:.1f}'


def _check_env(env_list, key, value_or_none):
    if value_or_none is None:
        assert not any(
            env.name == key
            for env in env_list
        )
    else:
        assert any(
            env.name == key and
            env.value == value_or_none
            for env in env_list
        )
