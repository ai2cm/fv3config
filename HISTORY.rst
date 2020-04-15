=======
History
=======

Latest
------

Major changes:
~~~~~~~~~~~~~
- filesystem operations now manually backoff with a 1-minute max time on RuntimeError (which gcsfs often raises when it shouldn't) and gcsfs.utils.HttpError
- `put_directory` now makes use of a thread pool to copy items in parallel.

Minor changes:
~~~~~~~~~~~~~
- `run_docker` now works when supplying an outdir on google cloud storage
- `put_directory` is now marked as package-private instead of module-private


v0.3.1 (2020-04-08)
-------------------

Major changes:
~~~~~~~~~~~~~
- Add get_timestep and config_from_yaml functions

Minor changes:
~~~~~~~~~~~~~
- Allow config_to_yaml to write to remote locations
- Control whether outputs are logged to console or not in `run_kubernetes`, `run_native`, and `run_docker`.

Breaking changes
~~~~~~~~~~~~~~~~
- Print stderr and stdout to the console by default when using fv3run. Use the
  `--capture-output` command-line flag to enable the previous behavior.


v0.3.0 (2020-04-03)
-------------------

Major changes:
~~~~~~~~~~~~~
- Added `--kubernetes` command-line flag to output a kubernetes config yaml to stdout

Minor changes:
~~~~~~~~~~~~~
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
