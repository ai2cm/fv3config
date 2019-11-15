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

    from fv3config import refresh_downloaded_data

    refresh_downloaded_data()

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
