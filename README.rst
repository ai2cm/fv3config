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

    import fv3config

    with open("config.yml", "r") as f:
        config = fv3config.load(f)
    fv3config.write_run_directory(config, './rundir')


:code:`config` is a configuration dictionary which contains namelists, input data specifications,
and other options. It can be edited just like any dictionary.

For more in-depth usage, please refer to the documentation. This can be generated with :code:`make docs`.


Authentication with Google Cloud Storage
----------------------------------------

Many of the examples in this repo refer to data stored in an Allen AI google
cloud storage bucket, which is open to the public...but not for free.

This package uses fsspec to access remote files. See their `configuration
documentation`_ for details. If you do not typically access AI2 google cloud
storage, you may need to enable requester pays, which you can do by setting the
following environment variables::

    export FSSPEC_GS_REQUESTER_PAYS=True
    # the following will be set with `gcloud auth login`
    export GOOGLE_CLOUD_PROJECT=<the project id to be charged>


You can check your authentication in a python console like this::

    >>> import google.auth
    >>> google.auth.default()
    (<google.oauth2.credentials.Credentials object at 0x7fdee0026dd0>, '<your project>')

If you see both the credentials object and the project id, you are adequately
authenticated for requester pays. If you are accessing a bucket owned by your
project, then the project does not need to be set.

.. _configuration documentation: https://filesystem-spec.readthedocs.io/en/latest/features.html#configuration