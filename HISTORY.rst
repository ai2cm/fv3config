History
=======

v0.6.0 (2021-02-22)
-------------------

Major changes:
~~~~~~~~~~~~~~

- add `DiagTable` class with associated `DiagFileConfig` and `DiagFieldConfig` dataclasses.
- make `fv3config.config_to_yaml` a public function.
- update `fv3config.config_to_yaml` and `fv3config.config_from_yaml` to go between
  `fv3config.DiagTable` and `dict` types as necessary when serializing/deserializing
- `write_run_directory` provisions necessary `patch_files` for config if the 
  `fv_core_nml.nudge` option is set to `True`.


v0.5.2 (2021-02-04)
-------------------

- Add logging to write_run_directory command

v0.5.1
------

- Fix formatting of this changelog for PyPI

v0.5.0
------

Breaking changes:
~~~~~~~~~~~~~~~~~
- enable_restart function now requires an initial_conditions argument. It also sets
  force_date_from_namelist to False.

Major changes:
~~~~~~~~~~~~~~

- a new public function `fv3config.get_bytes_asset_dict`
- a new command line interface `write_run_directory`
- removed integration tests for run_docker and run_native which actually executed the model
- all tests are now offline, using a mocked in-memory gcsfs to represent remote communication.
- add a Dockerfile to produce a lightweight image with fv3config installed

- Add new public functions `fv3config.get_nudging_assets` and `fv3config.update_config_for_nudging`.
- Add CLI entry points for enable_restart and update_config_for_nudging.

Minor changes:
~~~~~~~~~~~~~~
- updated create_rundir example to accept external arguments
- refactor get_current_date function to not require the path to the INPUT directory.

v0.4.0 (2020-07-09)
-------------------

Major changes:
~~~~~~~~~~~~~~
- the old "default" data options are removed
- orographic_forcing is now a required configuration key
- get_default_config() is removed, with a placeholder which says it was removed
- ensure_data_is_downloaded is removed, with a placeholder which says it was removed

v0.3.2 (2020-04-16)
-------------------

Major changes:
~~~~~~~~~~~~~~
- filesystem operations now manually backoff with a 1-minute max time on RuntimeError (which gcsfs often raises when it shouldn't) and gcsfs.utils.HttpError
- `put_directory` now makes use of a thread pool to copy items in parallel.

Minor changes:
~~~~~~~~~~~~~~
- `run_docker` now works when supplying an outdir on google cloud storage
- `put_directory` is now marked as package-private instead of module-private


v0.3.1 (2020-04-08)
-------------------

Major changes:
~~~~~~~~~~~~~~
- Add get_timestep and config_from_yaml functions

Minor changes:
~~~~~~~~~~~~~~
- Allow config_to_yaml to write to remote locations
- Control whether outputs are logged to console or not in `run_kubernetes`, `run_native`, and `run_docker`.

Breaking changes
~~~~~~~~~~~~~~~~
- Print stderr and stdout to the console by default when using fv3run. Use the
  `--capture-output` command-line flag to enable the previous behavior.


v0.3.0 (2020-04-03)
-------------------

Major changes:
~~~~~~~~~~~~~~
- Added `--kubernetes` command-line flag to output a kubernetes config yaml to stdout

Minor changes:
~~~~~~~~~~~~~~
- Added the flag ``--mca btl_vader_single_copy_mechanism none to mpirun in fv3run`` to mpirun in fv3run
- Add ReadTheDocs configuration file
- Do not require output dir and fv3config to be remote in ``run_kubernetes``
- Fix bug when submitting k8s jobs with images that have an "_" in them

Breaking changes
~~~~~~~~~~~~~~~~
- Refactored run_kubernetes and run_docker to call run_native via a new API serializing
  their args/kwargs as json strings. The
  fv3config version in a docker image must be greater than or equal inside a
  container to outside, or a silent error will occur.
- When output location is set to a local path, the job now runs in that output location instead of in a temporary directory which then gets copied. This is done both to reduce copying time for large jobs, and to improve visibility of model behavior while running.

0.2.0 (2020-01-27)
------------------

- Began tagging version commits


0.1.0 (2019-10-11)
------------------

- Initial pre-alpha release
