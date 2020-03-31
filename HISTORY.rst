=======
History
=======

latest
------

Minor changes:
~~~~~~~~~~~~~
* Added the flag ``--mca btl_vader_single_copy_mechanism none to mpirun in fv3run`` to mpirun in fv3run
* Add ReadTheDocs configuration file
* Do not require output dir and fv3config to be remote in ``run_kubernetes``
* Fix bug when submitting k8s jobs with images that have an "_" in them

Breaking changes
~~~~~~~~~~~~~~~~
* Refactored run_kubernetes and run_docker to call run_native via a new API serializing
  their args/kwargs as json strings. While no API changes occured, the
  fv3config version in a docker image must be greater than or equal inside a
  container to outside, or a silent error will occur.

0.2.0 (2020-01-27)
------------------

* Began tagging version commits


0.1.0 (2019-10-11)
------------------

* Initial pre-alpha release
