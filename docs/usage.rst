=====
Usage
=====

Quickstart
----------

The following code would write a run directory based on the contents of a yaml file::

    from fv3config import write_run_directory

    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)
    write_run_directory(config, './rundir')

:code:`config` is a configuration dictionary which contains namelists, input data specifications,
and other options, as described further below. It can be edited just like any dictionary. Namelists are specified as
sub-dictionaries. An example C12 configuration dictionary is in the `tests` directory of this package.

A run directory based on a configuration can be written using :py:func:`fv3config.write_run_directory`.

Shell Usage
-----------

This module installs a command line interface `write_run_directory` that can
be used to write the run directory from a shell. For example, if the file
`config.yaml` contains a yaml-encoded configuration dictionary

    write_run_directory config.yaml rundir

will write an FV3 run directory to the path `rundir`.

Two additional command line interfaces are useful for modifying configuration dictionaries
in order to use them for restart runs:

    enable_restart config.yaml /path/to/initial/conditions

and to provision the necessary files required for a nudged run:

    update_config_for_nudging config.yaml

Both of these shell commands will modify the given configuration dictionary in place.

This module also installs a command line interface `fv3run`, which is further detailed below.

Data Caching
------------

:code:`fv3config` can write files from local or remote locations. When remote locations
are used, the package first downloads the data to a local cache directory.

If the FV3CONFIG_CACHE_DIR environment variable is set, the package will download
and store data into ``$(FV3CONFIG_CACHE_DIR)/fv3config-cache``.
If unset, by default the package will use the "user cache" directory for the user's
operating system.

The download location can be retrieved using :py:func:`fv3config.get_cache_dir`, and set
manually using :py:func:`fv3config.set_cache_dir`. Note that the "fv3config-cache" subdirectory
will be appended to the cache directory you set. If the target is set to a directory
that already contains the archive download, it will automatically start using those
files. Conversely, if the target is set to an empty directory, it will be necessary
to re-download the cache files.

It's unlikely, but do not set the cache directory to a location that already contains
a "fv3config-cache" subdirectory with unrelated files, or the cache files will not
download until you call :py:func:`fv3config.refresh_downloaded_data` (which will delete any files
in the subdirectory).

Automatic caching of remote files can be disabled using the
:py:func:`fv3config.do_remote_caching` routine.


Configuration
-------------

The ``config`` dictionary must have at least the following items:

==================== ======================================== ============================================
Key                  Type                                     Description
==================== ======================================== ============================================
namelist             dict                                     Model namelist
experiment_name      str                                      Name of experiment to use in output
diag_table           str or :py:class:`~fv3config.DiagTable`  location of diag_table file, or one of ("default", "grid_spec", "no_output"), or DiagTable object
data_table           str                                      location of data_table file, or "default"
initial_conditions   str                                      location of directory containing initial conditions data
forcing              str                                      location of directory containing forcing data
orographic_forcing   str                                      location of directory containing orographic data
==================== ======================================== ============================================

Paths to files or directories on the local
filesystem must be given as absolute paths. If paths are given that begin with ``gs://`` then ``fv3config`` will
attempt to download the specified file or files from Google Cloud Storage. For this functionality, ``gcsfs``
must be installed and authorized to download from the specified bucket.

The ``namelist`` item is special in that it is explicitly stored in the ``config`` dictionary. For the
fv3gfs model, individual namelists are specified for various components of the model. As an example, the
vertical resolution can be accessed via ``config['namelist']['fv_core_nml']['npz']``.

The ``diag_table`` can be either be a tag or path to a file, or it can explicitly represent
the desired output diagnostics with a :py:class:`~fv3config.DiagTable` object. See a more complete
description of this object below.

By default, fv3config attempts to automatically select the ``field_table`` file
to use for the model based on the selected microphysics scheme in the
namelist. This supports Zhao-Carr or GFDL microphysics. If the user provides a
``field_table`` key indicating a filename in the configuration dictionary, that
file will be used instead.

.. note::
   The `Han and Bretherton (2019) <https://journals.ametsoc.org/doi/full/10.1175/WAF-D-18-0146.1>`_ TKE-EDMF
   boundary layer scheme requires an additional tracer to be defined in the
   ``field_table`` for TKE. This scheme is currently not supported by default
   in ``fv3config``; however for the time being one can supply a custom
   ``field_table`` for this purpose.

Some helper functions exist for editing and retrieving information from configuration
dictionaries, like :py:func:`fv3config.get_run_duration` and
:py:func:`fv3config.set_run_duration`. See the :ref:`API Reference` for more details.

Specifying individual files
---------------------------

More fine-grained control of the files that are written to the run-directory is possible using the "asset"
representation of run-directory files. An asset is a dictionary that knows about one files's source
location/filename, target filename, target location within the run directory and whether that file is copied or linked.
Asset dicts can be generated with the helper function :py:func:`fv3config.get_asset_dict`. For example::

    >>> get_asset_dict('/path/to/filedir/', 'sample_file.nc', target_location='INPUT/')
    {'source_location': '/path/to/filedir/',
    'source_name': 'sample_file.nc',
    'target_location': 'INPUT/',
    'target_name': 'sample_file.nc',
    'copy_method': 'copy'}

One can also add specify the asset as a python bytes object that will be
written to the desired location using
:py:func:`fv3config.get_bytes_asset_dict`. For example::

    >>> get_bytes_asset_dict(b"hello_world", "hello.txt", target_location=".")

This is useful for storing small files in the configuration dictionary,
without needing to deploy them to an external storage system.

One can set ``config['initial_conditions']`` or ``config['forcing']``
to a list of assets in order to specify every initial condition or forcing file individually.

One can use a directory to specify the initial conditions or forcing files and replace only a
subset of the files within the that directory with the optional ``config['patch_files']`` item.
All assets defined in ``config['patch_files']`` will overwrite any files specified in the
initial conditions or forcing if they have the same target location and name.

DiagTable configuration
-----------------------

The ``diag_table`` specifies the diagnostics to be output by the Fortran model. See documentation
for the string representation of the ``diag_table``
`here <https://mom6.readthedocs.io/en/latest/api/generated/pages/Diagnostics.html>`_. The fv3config
package defines a python representation of this object, :py:class:`~fv3config.DiagTable`, which can
be used to explicitly represent the ``diag_table`` within an fv3config configuration dictionary.

The ``DiagTable`` object can be initialized from a dict (here serialized as YAML) as follows. Suppose
the following is saved within ``sample_diag_table.yaml``:

.. code-block:: yaml

    name: example_diag_table
    base_time: 2000-01-01 00:00:00
    file_configs:
    - name: physics_diagnostics
      frequency: 1
      frequency_units: hours
      field_configs:
      - field_name: totprcpb_ave
        module_name: gfs_phys
        output_name: surface_precipitation_rate
      - field_name: ULWRFtoa
        module_name: gfs_phys
        output_name: upward_longwave_radiative_flux_at_toa

Then a ``DiagTable`` object can be initialized as:

.. code-block:: python

    >>> import fv3config
    >>> import yaml
    >>> with open("sample_diag_table.yaml") as f:
            diag_table_dict = yaml.safe_load(f)
    >>> diag_table = fv3config.DiagTable.from_dict(diag_table_dict)
    >>> print(diag_table)  # will output diag_table in format expected by Fortran model
    example_diag_table
    2000 1 1 0 0 0

    "physics_diagnostics", 1, "hours", 1, "hours", "time"

    "gfs_phys", "totprcpb_ave", "surface_precipitation_rate", "physics_diagnostics", "all", "none", "none", 2
    "gfs_phys", "ULWRFtoa", "upward_longwave_radiative_flux_at_toa", "physics_diagnostics", "all", "none", "none", 2

The same ``DiagTable`` can also be initialized programmatically as follows:

.. code-block:: python

    >>> import fv3config
    >>> import datetime
    >>> diag_table = fv3config.DiagTable(
            name="example_diag_table",
            base_time=datetime.datetime(2000, 1, 1)
            file_configs=[
                fv3config.DiagFileConfig(
                    name="physics_diagnostics",
                    frequency=1,
                    frequency_units="hours",
                    field_configs=[
                        fv3config.DiagFieldConfig(
                            "gfs_phys",
                            "totprcb_ave"
                            "surface_precipitation_rate"
                        ),
                        fv3config.DiagFieldConfig(
                            "gfs_phys",
                            "ULWRFtoa"
                            "upward_longwave_radiative_flux_at_toa"
                        ),
                    ]
                )
            ]
        )

String representations of the ``diag_table`` (i.e. those expected by the Fortran model) can be parsed
with the :py:meth:`fv3config.DiagTable.from_str` method.

If serializing an ``fv3config`` configuration object to yaml it is recommended to use
:py:meth:`fv3config.config_to_yaml`. This method will convert any ``DiagTable`` instances to
dicts (using :py:meth:`fv3config.DiagTable.asdict`), which can be safely serialized.


Running the model with fv3run
-----------------------------

`fv3config` provides a tool for running the python-wrapped model called `fv3run`.
For example, you can run the default configuration using first::

    $ docker pull us.gcr.io/vcm-ml/fv3gfs-python

to acquire the docker image for the python wrapper, followed by
a call to :py:func:`fv3config.run_docker`:

.. code-block:: python

    >>> import fv3config
    >>> import yaml
    >>> with open("config.yml", 'r') as f:
    >>>     config = yaml.safe_load(f)
    >>> fv3config.run_docker(config, 'outdir', docker_image='us.gcr.io/vcm-ml/fv3gfs-python')

If the ``fv3gfs-python`` package is installed natively, the model could be run
using :py:func:`fv3config.run_native`:

.. code-block:: python

    >>> fv3config.run_native(config, 'outdir')

The python config can be passed as either a configuration dictionary, or the name of
a yaml file. There is also a bash interface for running from yaml configuration.

.. code-block:: bash

    $ fv3run --help
    usage: fv3run [-h] [--runfile RUNFILE] [--dockerimage DOCKERIMAGE]
                  [--keyfile KEYFILE]
                  config outdir

    Run the FV3GFS model. Will use google cloud storage key at
    $GOOGLE_APPLICATION_CREDENTIALS by default.

    positional arguments:
      config                location of fv3config yaml file
      outdir                location to copy final run directory, used as run
                            directory if local


    optional arguments:
      -h, --help            show this help message and exit
      --runfile RUNFILE     location of python script to execute with mpirun
      --dockerimage DOCKERIMAGE
                            if passed, execute inside a docker image with the
                            given name
      --keyfile KEYFILE     google cloud storage key to use for cloud copy
                            commands
      --kubernetes          if given, ignore --keyfile and output a yaml
                            kubernetes config to stdout instead of submitting a
                            run

The only required inputs are ``config``, which specifies a yaml file containing the
``fv3config`` run directory configuration, and a final location to copy the run directory.
A keyfile can be specified to authenticate Google cloud storage for any data sources
located in Google cloud buckets, or the key is taken from an environment variable
by default. If ``dockerimage`` is specified, the command will run inside a Docker
container based on the given image name. This assumes the ``fv3config`` package and
``fv3gfs`` python wrapper are installed inside the container, along with any
dependencies.

The python interface is very similar to the command-line interface, but is split into
separate functions based on where the model is being run.

Customizing the model execution
-------------------------------

The ``runfile`` is the python script that will be executed by mpi, which
typically imports the ``fv3gfs`` module, and then performs some time stepping.
The default behavior is to use a pre-packaged runfile which reproduces the
behavior of Fortran model identically. For additional, flexibility a custom
runfile can be specified as an argument to all the ``run_`` functions.


The environmental variable ``FV3CONFIG_DEFAULT_RUNFILE`` can be used to override
the default runfile. If set, this variable should contain the path of the
runfile.

.. note::

  When using ``run_docker`` or ``run_kubernetes``, the value of
  ``FV3CONFIG_DEFAULT_RUNFILE`` and the file it points to will be read inside the
  docker image where execution occurs. It will have no effect if set on the host
  system outside of the docker image.

Submitting a Kubernetes job
---------------------------

A python interface :py:func:`fv3config.run_kubernetes` is provided for
submitting `fv3run` jobs to Kubernetes. Here's an example for submitting a job
based on a config dictionary stored in Google cloud storage::

    import yaml
    import gcsfs
    import fv3config

    config_location = 'gs://my_bucket/fv3config.yml'
    outdir = 'gs://my_bucket/rundir'
    docker_image = 'us.gcr.io/vcm-ml/fv3gfs-python'

    fv3config.run_kubernetes(
        config_location,
        outdir,
        docker_image,
        gcp_secret='gcp-key'  # replace with your kubernetes secret
                              # containing gcp key in key.json
    )

The gcp key is generally necessary to gain permissions to read and write from google
cloud storage buckets. In the unlikely case that you are writing to a public bucket,
it can be ommitted.

From the command line, fv3run can be used to create a yaml file to submit for a
kubernetes job. To create the file, add the ``--kubernetes`` flag to ``fv3run`` and
pipe the result to a file. For example:

  $ fv3run gs://bucket/config.yml gs://bucket/outdir --dockerimage us.gcr.io/vcm-ml/fv3gfs-python:latest --kubernetes > kubeconfig.yml

The resulting file can be submitted using

  $ kubectl apply -f kubeconfig.yml

You can also modify the yaml file before submitting the job, for example to request more
than one processor or a different amount of memory.

Restart runs
------------

The required namelist settings for a restart run (as opposed to a run initialized from an observational
analysis) can be applied to a configuration dictionary as follows::

    config = enable_restart(config, initial_conditions)

Nudging
-------

The fv3gfs model contains a module for nudging the state of the atmosphere towards
GFS analysis. Two public functions are provided to ease the configuration of nudging runs.

Given the run duration and start date, :py:func:`fv3config.get_nudging_assets`
returns a list of fv3config assets corresponding to the GFS analysis files required. Given
an fv3config object, :py:func:`fv3config.update_config_for_nudging` will add the necessary
assets and namelist options for a nudging run. This function requires that the fv3config
object contains a `gfs_analysis_data` entry with corresponding `url` and `filename_pattern`
items.