import os
from ._docker import _run_in_docker
from ._native import _run_native


def run(config_dict_or_location, outdir, runfile=None, dockerimage=None, keyfile=None):
    if keyfile is None:
        keyfile = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', None)
    if dockerimage is not None:
        _run_in_docker(
            config_dict_or_location, outdir, dockerimage,
            runfile=runfile, keyfile=keyfile
        )
    else:
        _run_native(config_dict_or_location, outdir, runfile=runfile)
