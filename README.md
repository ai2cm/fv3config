FV3Config
=========


FV3Config is used to configure and manipulate run directories for FV3GFS.

This package is currently under development, right now this README serves as a place
to track design decisions.

Some features needed:

* create a new run directory
* prepare a run directory for resubmission
    * move restart files from RESTART to INPUT
    * move output files to a location where they will not be overwritten
* modify configuration in an existing run directory

How to specify run directory configuration is an open design question. A likely
option is in dictionaries. You can pass values from a dictionary `config` to a
function `func` using `func(**config)`. yaml files can be loaded into a dictionary.

Namelist manipulation can be done with an existing package, like
[f90nml`](https://github.com/marshallward/f90nml).


* Free software: BSD license


Features
--------

* TODO
