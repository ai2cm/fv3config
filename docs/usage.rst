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

Configuration
-------------

The ``config`` dictionary must have at least the following items:

==================== ======== ==================== ========================
Key                  Type     Default              Other built-in options
==================== ======== ==================== ========================
namelist             Namelist default Namelist     none
initial_conditions   str      'gfs_example'        'restart_example'
diag_table           str      'default'            'grid_spec', 'no_output'
data_table           str      'default'            none
experiment_name      str      'default_experiment' n/a
forcing              str      'default'            none
==================== ======== ==================== ========================

In addition to one of the built-in options, a custom ``diag_table`` and ``data_table`` can be specified
by supplying a path to a file. Custom ``initial_conditions`` and ``forcing`` can be specified by
supplying a path to a directory with the appropriate initial conditions files and forcing files,
respectively. Paths must be given as absolute paths.

The ``namelist`` item is special in that it is explicitly stored in the ``config`` dictionary. For the
fv3gfs model, individual namelists are specified for various components of the model. As an example, the
vertical resolution can be accessed via ``config['namelist']['fv_core_nml']['npz']``.
