import os
import uuid
from .._exceptions import DelayedImportError
from .. import filesystem
from ._docker import _get_runfile_args, _get_python_command
try:
    import kubernetes as kube
except ImportError as err:
    kube = DelayedImportError(err)


def _ensure_is_remote(location, description):
    if not filesystem._is_gcloud_path(location):
        raise ValueError(
            f'{description} must be on Google cloud when running on kubernetes, '
            f'instead is {location}'
        )


def run_kubernetes(
        config_location, outdir, docker_image, runfile=None, jobname=None,
        namespace="default", google_cloud_project=None,
        memory_gb=3.6, memory_gb_limit=None, cpu_count=1, gcp_secret=None,
        image_pull_policy='IfNotPresent'):
    """Submit a kubernetes job to perform a fv3run operation.

    Much of the configuration must be first saved to google cloud storage, and then
    supplied via paths to that configuration. The resulting run directory is copied
    out to a google cloud storage path. This call is non-blocking, and only submits
    a job.

    Args:
        config_location (str): google cloud storage location of a yaml file containing
            a configuration dictionary
        outdir (str): google cloud storage location to upload
            the resulting run directory
        docker_image (str): docker image name to use for execution, which has fv3config
            installed with fv3run
        runfile (str, optional): google cloud storage location of a python file to
            execute as the model executable
        jobname (str, optional): name to use for the kubernetes job, defaults to a
            random uuid.uuid4().hex
        namespace (str, optional): kubernetes namespace for the job,
            defaults to "default"
        google_cloud_project (str, optional): value for GOOGLE_CLOUD_PROJECT environment
            variable when running the kubernetes job, which is used by gcsfs for
            some operations. By default the environment variable is unset.
        memory_gb (float, optional): gigabytes of memory required for the kubernetes
            worker, defaults to 3.6GB
        memory_gb_limit (float, optional): maximum memory allowed for the kubernetes
            worker, defaults to the value set by memory_gb
        cpu_count (int, optional): number of CPUs to use on the kubernetes worker
        gcp_secret (str, optional): name of kubernetes secret to mount containing a
            file ``key.json`` to use as the google cloud storage key.
        image_pull_policy (str, optional): pull policy passed on to the kubernetes job.
            if set to "Always", will always pull the latest image. When "IfNotPresent",
            will only pull if no image has already been pulled.
            Defaults to "IfNotPresent".
    """
    if google_cloud_project is None:
        try:
            google_cloud_project = filesystem._get_gcloud_project()
        except ImportError:
            google_cloud_project = None
    if jobname is None:
        jobname = uuid.uuid4().hex
    for location, description in (
            (config_location, 'yaml configuration'),
            (outdir, 'output directory'),
            (runfile, 'runfile')):
        if location is not None:
            _ensure_is_remote(location, description)
    if memory_gb_limit is None:
        memory_gb_limit = memory_gb
    job = _create_job_object(
        config_location, outdir, docker_image, runfile, jobname,
        memory_gb, memory_gb_limit, cpu_count, gcp_secret, google_cloud_project,
        image_pull_policy=image_pull_policy)
    _submit_job(job, namespace)


def _submit_job(job, namespace):
    kube.config.load_kube_config()
    api = kube.client.BatchV1Api()
    api.create_namespaced_job(body=job, namespace=namespace)


def _get_kube_command(config_location, outdir, runfile=None):
    bind_mount_args = []
    python_args = []
    _get_runfile_args(runfile, bind_mount_args, python_args)
    python_command = _get_python_command(config_location, outdir)
    assert bind_mount_args == [], bind_mount_args
    return python_command + python_args


def _create_job_object(
        config_location, outdir, docker_image, runfile, jobname,
        memory_gb, memory_gb_limit, cpu_count, gcp_secret=None,
        google_cloud_project=None, image_pull_policy='IfNotPresent'):
    resource_requirements = kube.client.V1ResourceRequirements(
        limits={
            'memory': f'{memory_gb_limit:.1f}G',
        },
        requests={
            'memory': f'{memory_gb:.1f}G',
            'cpu': f'{cpu_count:.1f}'
        },
    )
    env_list = []
    if gcp_secret is not None:
        env_list, volume_list, volume_mounts_list = _get_secret_args(gcp_secret)
    else:
        env_list, volume_list, volume_mounts_list = [], [], []
    if google_cloud_project is not None:
        env_list.append(
            kube.client.V1EnvVar(
                name='GOOGLE_CLOUD_PROJECT',
                value=google_cloud_project,
            )
        )
    container = kube.client.V1Container(
        name=os.path.basename(docker_image),
        image=docker_image,
        image_pull_policy=image_pull_policy,
        command=_get_kube_command(config_location, outdir, runfile),
        resources=resource_requirements,
        volume_mounts=volume_mounts_list,
        env=env_list,
    )
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


def _get_secret_args(gcp_secret):
    env_list = [
        kube.client.V1EnvVar(
            name='GOOGLE_APPLICATION_CREDENTIALS',
            value='/secret/gcp-credentials/key.json',
        ),
        kube.client.V1EnvVar(
            name='CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE',
            value='/secret/gcp-credentials/key.json',
        )
    ]
    volume = kube.client.V1Volume(
        name='gcp-key-secret',
        secret=kube.client.V1SecretVolumeSource(
            secret_name=gcp_secret
        )
    )
    volume_list = [volume]
    volume_mounts_list = [
        kube.client.V1VolumeMount(
            mount_path='/secret/gcp-credentials',
            name=volume.name,
            read_only=True,
        ),
    ]
    return env_list, volume_list, volume_mounts_list
