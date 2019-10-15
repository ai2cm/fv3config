# -*- coding: utf-8 -*-

"""Main module."""
import os

namelist_defaults = {}

def register_config_option(name, default_value, description):
    pass


class RunConfig(object):

    def __init__(self, input_data=None, forcing_data=None, config=None):
        self._config = config or ConfigDict()
        self._input_data = input_data or StateData.from_config(self._config)
        self._forcing_data = forcing_data or ForcingData.from_config(self._config)
        self._namelist_file = NamelistFile(self._config)

    @classmethod
    def from_directory(cls, dirname):
        return cls(
            target_directory=dirname,
            input_data=StateData.from_directory(dirname),
            forcing_data=ForcingData.from_directory(dirname),
            config=ConfigDict.from_directory(dirname)
        )

    @property
    def config(self):
        # must be property so it can't be replaced, so that the instance we have is the
        # same instance as held by self._namelist_file.
        return self._config

    @property
    def input_data(self):
        return self._input_data

    @input_data.setter
    def input_data(self, input_data):
        self._input_data = input_data

    def write(self, target_directory):
        self._forcing_data.link(target_directory)
        self._input_data.write(target_directory)
        self._namelist_file.save(os.path.join(target_directory, 'input.nml'))


class StateData(object):

    def __init__(self, data_directory):
        self._data_directory = data_directory

    @classmethod
    def from_directory(cls, dirname):
        pass

    @classmethod
    def from_config(cls, config):
        pass

    def write(self, target_directory, config):
        # special case when data_directory is target_directory, just check if config is compatible
        # with what's on disk.
        pass


class ConfigDict(object):

    def __init__(self):
        self._dict = {}

    @classmethod
    def from_directory(cls, dirname):
        cls.from_namelist(os.path.join(dirname, 'input.nml'))

    @classmethod
    def from_namelist(cls, filename):
        pass

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        if key not in self._dict and key in namelist_defaults:
            return namelist_defaults[key]
        else:
            return self._dict[key]

    def to_namelist(self, namelist_filename):
        pass


class ForcingData(object):

    @classmethod
    def from_directory(cls, dirname):
        pass

    def link(self, target_directory):
        pass
