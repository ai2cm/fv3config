FV3Config
=========

.. image:: https://readthedocs.org/projects/fv3config/badge/?version=latest
   :target: https://fv3config.readthedocs.io/en/latest/?badge=latest
   
.. image:: https://circleci.com/gh/VulcanClimateModeling/fv3config.svg?style=svg
   :target: https://circleci.com/gh/VulcanClimateModeling/fv3config

FV3Config is used to configure and manipulate run directories for FV3GFS.

* Free software: BSD license

Basic usage
-----------

.. code-block:: python

    from fv3config import write_run_directory

    with open("config.yml", 'r') as f:
        config = yaml.safe_load(f)
    write_run_directory(config, './rundir')

:code:`config` is a configuration dictionary which contains namelists, input data specifications,
and other options. It can be edited just like any dictionary.

For more in-depth usage, please refer to the documentation. This can be generated with :code:`make docs`.
