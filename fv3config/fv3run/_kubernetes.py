import os
import copy
from .._exceptions import DelayedImportError
from .gcloud import _is_gcloud_path
from ._docker import _get_runfile_args, _get_python_command

try:
    import kubernetes as kube
except ImportError as err:
    kube = DelayedImportError(err)

JOB_NAMESPACE = "kubeflow"


def _ensure_is_remote(location, description):
    if not _is_gcloud_path(location):
        raise ValueError(
            f'{description} must be on Google cloud when running on kubernetes, '
            f'instead is {location}'
        )


def run_kubernetes(
        config_location, outdir, docker_image, runfile=None, jobname=None,
        memory_gb=3.6, memory_gb_limit=None, cpu_count=1, gcp_secret=None):
    """[summary]

    [description]
    gcp_secret (str, optional): the name of a secret containing a GCP key named user-gcp-sa.json
    """
    for location, description in (
            (config_location, 'yaml configuration'),
            (outdir, 'output directory'),
            (runfile, 'runfile')):
        _ensure_is_remote(location, description)
    if memory_gb_limit is None:
        memory_gb_limit = memory_gb
    kube.config.load_kube_config()
    api = kube.client.BatchV1Api()
    job = _create_job_object(
        config_location, outdir, docker_image, runfile, jobname,
        memory_gb, memory_gb_limit, cpu_count, gcp_secret)
    api.create_namespaced_job(body=job, namespace=JOB_NAMESPACE)


def _get_kube_command(config_location, outdir, runfile=None):
    bind_mount_args = []
    python_args = []
    _get_runfile_args(runfile, bind_mount_args, python_args)
    python_command = _get_python_command(config_location, outdir)
    assert bind_mount_args == [], bind_mount_args
    return python_command + python_args


def _create_job_object(
        config_location, outdir, docker_image, runfile, jobname,
        memory_gb, memory_gb_limit, cpu_count, gcp_secret=None):
    resource_requirements = kube.client.V1ResourceRequirements(
        limits={
            'memory': f'{memory_gb_limit:.1f}G',
        },
        requests={
            'memory': f'{memory_gb:.1f}G',
            'cpu': f'{cpu_count:.1f}'
        },
    )
    container = kube.client.V1Container(
        name=os.path.basename(docker_image),
        image=docker_image,
        command=_get_kube_command(config_location, outdir, runfile),
        resources=resource_requirements,
        volume_mounts=[
            kube.client.V1VolumeMount(
                mount_path='/secret/gcp-credentials',
                name='gcp-credentials-user-gcp-sa'
            ),
        ],
    )
    if gcp_secret is not None:
        container.env = [
            kube.client.V1EnvVar(
                name='GOOGLE_APPLICATION_CREDENTIALS',
                value='/secret/gcp-credentials/user-gcp-sa.json',
            ),
            kube.client.V1EnvVar(
                name='CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE',
                value='/secret/gcp-credentials/user-gcp-sa.json',
            )
        ]
        volume = kube.client.V1Volume(
            name='gcp-credentials-user-gcp-sa',
            secret=kube.client.V1SecretVolumeSource(
                secret_name=gcp_secret
            )
        )
        volume_list = [volume]
    else:
        volume_list = []
    pod_spec = kube.client.V1PodSpec(
        restart_policy="Never", containers=[container], volumes=volume_list,
    )
    template_spec = kube.client.V1PodTemplateSpec(
        metadata=kube.client.V1ObjectMeta(labels={"app": 'fv3run'}),
        spec=pod_spec,
    )
    job_spec = kube.client.V1JobSpec(
        template=template_spec,
        backoff_limit=0,
        completions=1,
        ttl_seconds_after_finished=100,
    )
    job = kube.client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=kube.client.V1ObjectMeta(
            name=jobname,
        ),
        spec=job_spec,
    )
    return job
