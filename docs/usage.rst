=====
Usage
=====

Quickstart
----------

The following code would write a default run directory::

    from fv3config import get_default_config, write_run_directory

    config = get_default_config()
    write_run_directory(config, './rundir')

:code:`config` is a configuration dictionary which contains namelists, input data specifications,
and other options. It can be edited just like any dictionary. Namelists are specified as
sub-dictionaries.

Data Caching
------------

:code:`fv3config` writes run directories by symbolically linking cached data files into the directory.
Before this data can be linked, it must be downloaded. This can be done form the command line:

.. code-block:: console

    $ python -m fv3config.download_data

Or from inside Python::

    from fv3config import ensure_data_is_downloaded

    ensure_data_is_downloaded()

It is also possible to delete and re-download the data archive, in case something goes wrong::

    $ python -m fv3config.refresh_data

Cache Location
--------------

If the FV3CONFIG_CACHE_DIR environment variable is set, the package will download
and store data into `$(FV3CONFIG_CACHE_DIR)/fv3config-cache`.
If unset, by default the package will use the "user cache" directory for the user's
operating system.

The download location can be retrieved using `fv3config.get_cache_dir()`, and set
manually using `fv3config.set_cache_dir()`. Note that the "fv3config-cache" subdirectory
will be appended to the cache directory you set. If the target is set to a directory
that already contains the archive download, it will automatically start using those
files. Conversely, if the target is set to an empty directory, it will be necessary
to re-download the cache files.

It's unlikely, but do not set the cache directory to a location that already contains
a "fv3config-cache" subdirectory with unrelated files, or the cache files will not
download until you call `refresh_downloaded_data` (which will delete any files
in the subdirectory).

Configuration
-------------

The ``config`` dictionary must have at least the following items:

==================== ======== ==================== ========================
Key                  Type     Default              Other built-in options
==================== ======== ==================== ========================
namelist             Namelist default Namelist     none
experiment_name      str      'default_experiment' n/a
diag_table           str      'default'            'grid_spec', 'no_output'
data_table           str      'default'            none
initial_conditions   str      'gfs_example'        'restart_example'
forcing              str      'default'            none
==================== ======== ==================== ========================

In addition to one of the built-in options, a custom ``diag_table`` and ``data_table`` can be specified
by supplying a path to a file. Custom ``initial_conditions`` and ``forcing`` can be specified by
supplying a path to a directory that contains the appropriate files. Paths to files or directories on the local
filesystem must be given as absolute paths. If paths are given that begin with ``gs://`` then ``fv3config`` will
attempt to download the specified file or files from Google Cloud Storage. For this functionality, ``gsutil``
must be installed and authorized to download from the specified bucket.

The ``namelist`` item is special in that it is explicitly stored in the ``config`` dictionary. For the
fv3gfs model, individual namelists are specified for various components of the model. As an example, the
vertical resolution can be accessed via ``config['namelist']['fv_core_nml']['npz']``.

Running the model with fv3run
-----------------------------

`fv3config` provides a tool for running the python-wrapped model called `fv3run`.
For example, you can run the default configuration using first::

    $ docker pull us.gcr.io/vcm-ml/fv3gfs-python

to acquire the docker image for the python wrapper, followed by::

    >>> import fv3config
    >>> config = fv3config.get_default_config
    >>> fv3config.run(config, 'outdir', docker_image='us.gcr.io/vcm-ml/fv3gfs-python')

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
      outdir                location to copy final run directory

    optional arguments:
      -h, --help            show this help message and exit
      --runfile RUNFILE     location of python script to execute with mpirun
      --dockerimage DOCKERIMAGE
                            if passed, execute inside a docker image with the
                            given name
      --keyfile KEYFILE     google cloud storage key to use for cloud copy
                            commands

The only required inputs are ``config``, which specifies a yaml file containing the
``fv3config`` run directory configuration, and a final location to copy the run directory.
A keyfile can be specified to authenticate Google cloud storage for any data sources
located in Google cloud buckets, or the key is taken from an environment variable
by default. If ``dockerimage`` is specified, the command will run inside a Docker
container based on the given image name. This assumes the ``fv3config`` package and
``fv3gfs`` python wrapper are installed inside the container, along with any
dependencies.

The python interface is very similar to the command-line interface.

.. autofunction:: fv3config.run

Restart runs
------------

The required namelist settings for a restart run (as opposed to a run initialized from an observational
analysis) can be applied to a configuration dictionary as follows::

    config = enable_restart(config)

A set of restart files is provided in the cached data files. Thus, an example run directory with model
restart initial conditions can be created with::

    from fv3config import get_default_config, write_run_directory, enable_restart

    config = get_default_config()
    config['initial_conditions'] = 'restart_example'
    config = enable_restart(config)
    write_run_directory(config, './rundir')
