import os
import re
import uuid
from .._exceptions import DelayedImportError
from .. import filesystem
from ._docker import _get_python_command

try:
    import kubernetes as kube
except ImportError as err:
    kube = DelayedImportError(err)


def run_kubernetes(
    config_location,
    outdir,
    docker_image,
    runfile=None,
    jobname=None,
    namespace="default",
    memory_gb=3.6,
    memory_gb_limit=None,
    cpu_count=1,
    gcp_secret=None,
    image_pull_policy="IfNotPresent",
):
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
        runfile (str, optional): location of a python file to
            execute as the model executable, either on google cloud storage or within
            the specified docker image
        jobname (str, optional): name to use for the kubernetes job, defaults to a
            random uuid.uuid4().hex
        namespace (str, optional): kubernetes namespace for the job,
            defaults to "default"
        memory_gb (float, optional): gigabytes of memory required for the kubernetes
            worker, defaults to 3.6GB
        memory_gb_limit (float, optional): maximum memory allowed for the kubernetes
            worker, defaults to the value set by memory_gb
        cpu_count (int, optional): number of CPUs to use on the kubernetes worker
        gcp_secret (str, optional): name of kubernetes secret to mount containing a
            file ``key.json`` to use as the google cloud storage key.
        image_pull_policy (str, optional): pull policy passed on to the
            kubernetes job. if set to "Always", will always pull the latest image.
            When "IfNotPresent", will only pull if no image has already been pulled.
            Defaults to "IfNotPresent".
    """
    job = _get_job(
        config_location,
        outdir,
        docker_image,
        runfile,
        jobname,
        memory_gb,
        memory_gb_limit,
        cpu_count,
        gcp_secret,
        image_pull_policy,
    )
    _submit_job(job, namespace)


def _get_job(
    config_location,
    outdir,
    docker_image,
    runfile=None,
    jobname=None,
    memory_gb=3.6,
    memory_gb_limit=None,
    cpu_count=1,
    gcp_secret=None,
    image_pull_policy="IfNotPresent",
):
    _ensure_locations_are_remote(config_location, outdir)
    kube_config = KubernetesConfig(
        jobname, memory_gb, memory_gb_limit, cpu_count, gcp_secret, image_pull_policy
    )
    return _create_job_object(
        config_location, outdir, docker_image, runfile, kube_config
    )


def _ensure_locations_are_remote(config_location, outdir):
    for location, description in (
        (config_location, "yaml configuration"),
        (outdir, "output directory"),
    ):
        if location is not None:
            _ensure_is_remote(location, description)


def _ensure_is_remote(location, description):
    if filesystem._is_local_path(location):
        raise ValueError(
            f"{description} must be a remote path when running on kubernetes, "
            f"instead is {location}"
        )


def _submit_job(job, namespace):
    kube.config.load_kube_config()
    api = kube.client.BatchV1Api()
    api.create_namespaced_job(body=job, namespace=namespace)


def _create_job_object(config_location, outdir, docker_image, runfile, kube_config):
    container = kube.client.V1Container(
        name=_get_name_from_image(docker_image),
        image=docker_image,
        image_pull_policy=kube_config.image_pull_policy,
        command=_get_kube_command(config_location, outdir, runfile),
        resources=kube_config.resource_requirements,
        volume_mounts=kube_config.volume_mounts,
        env=kube_config.env,
    )
    return _container_to_job(container, kube_config)


def _get_name_from_image(docker_image):
    name = os.path.basename(docker_image)
    return re.split("\W+", name)[0]


def _get_kube_command(config_location, outdir, runfile=None):
    if runfile is None:
        python_args = []
    else:
        python_args = ["--runfile", runfile]
    python_command = _get_python_command(config_location, outdir)
    return python_command + python_args


def _container_to_job(container, kube_config):
    # Toleration allows operation on the bigger nodes (with the specified taint)
    toleration = kube.client.V1Toleration(
        effect="NoSchedule", key="dedicated", value="climate-sim-pool",
    )
    pod_spec = kube.client.V1PodSpec(
        restart_policy="Never",
        containers=[container],
        volumes=kube_config.volumes,
        tolerations=[toleration],
    )
    template_spec = kube.client.V1PodTemplateSpec(
        metadata=kube.client.V1ObjectMeta(labels={"app": "fv3run"}), spec=pod_spec,
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
        metadata=kube.client.V1ObjectMeta(name=kube_config.jobname,),
        spec=job_spec,
    )
    return job


class KubernetesConfig:
    def __init__(
        self,
        jobname=None,
        memory_gb=3.6,
        memory_gb_limit=None,
        cpu_count=1,
        gcp_secret=None,
        image_pull_policy="IfNotPresent",
    ):
        """Container for kubernetes-specific job configuration.

        Args:
            jobname (str, optional): name to use for the kubernetes job, defaults to a
                random uuid.uuid4().hex
            memory_gb (float, optional): gigabytes of memory required for the kubernetes
                worker, defaults to 3.6GB
            memory_gb_limit (float, optional): maximum memory allowed for the kubernetes
                worker, defaults to the value set by memory_gb
            cpu_count (int, optional): number of CPUs to use on the kubernetes worker
            gcp_secret (str, optional): name of kubernetes secret to mount containing a
                file ``key.json`` to use as the google cloud storage key.
            image_pull_policy (str, optional): pull policy passed on to the
                kubernetes job. if set to "Always", will always pull the latest image.
                When "IfNotPresent", will only pull if no image has already been pulled.
                Defaults to "IfNotPresent".
        """
        if jobname is None:
            self.jobname = uuid.uuid4().hex
        else:
            self.jobname = jobname
        self.memory_gb = memory_gb
        if memory_gb_limit is None:
            self.memory_gb_limit = memory_gb
        else:
            self.memory_gb_limit = memory_gb_limit
        self.cpu_count = cpu_count
        self.gcp_secret = gcp_secret
        self.image_pull_policy = image_pull_policy

    @property
    def resource_requirements(self):
        return kube.client.V1ResourceRequirements(
            limits={"memory": f"{self.memory_gb_limit:.1f}G"},
            requests={
                "memory": f"{self.memory_gb:.1f}G",
                "cpu": f"{self.cpu_count:.1f}",
            },
        )

    @property
    def _secret_volume(self):
        if self.gcp_secret is not None:
            return kube.client.V1Volume(
                name="gcp-key-secret",
                secret=kube.client.V1SecretVolumeSource(secret_name=self.gcp_secret),
            )
        else:
            return None

    @property
    def volumes(self):
        if self.gcp_secret is not None:
            return [self._secret_volume]
        else:
            return []

    @property
    def volume_mounts(self):
        if self.gcp_secret is not None:
            volume_mounts = [
                kube.client.V1VolumeMount(
                    mount_path="/secret/gcp-credentials",
                    name=self._secret_volume.name,
                    read_only=True,
                )
            ]
        else:
            volume_mounts = []
        return volume_mounts

    @property
    def env(self):
        if self.gcp_secret is not None:
            return [
                kube.client.V1EnvVar(
                    name="GOOGLE_APPLICATION_CREDENTIALS",
                    value="/secret/gcp-credentials/key.json",
                ),
                kube.client.V1EnvVar(
                    name="CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE",
                    value="/secret/gcp-credentials/key.json",
                ),
            ]
        else:
            return []
