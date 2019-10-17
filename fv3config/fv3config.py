# -*- coding: utf-8 -*-

"""Main module."""
import os
import f90nml

class InvalidFileError(Exception):
    pass


def default_config_dict():
    return {}


class RunConfig(object):

    def __init__(self, input_data=None, forcing_data=None, config=None):
        if config is None:
            self._config = default_config_dict()
        else:
            self._config = config
        self._input_data = input_data or StateData.from_config(self._config)
        self._forcing_data = forcing_data or ForcingData.from_config(self._config)
        self._namelist_file = NamelistFile(self._config)

    @classmethod
    def from_directory(cls, dirname):
        return cls(
            target_directory=dirname,
            input_data=StateData.from_directory(os.path.join(dirname, 'INPUT')),
            forcing_data=ForcingData.from_directory(dirname),
            config=ConfigDict.from_directory(dirname)
        )

    @property
    def config(self):
        # must be property so it can't be replaced, so that the instance we have is the
        # same instance as held by self._namelist_file.
        return self._config

    @config.setter
    def config(self, config):
        # must be property so it can't be replaced, so that the instance we have is the
        # same instance as held by self._namelist_file.
        self._config.clear()
        return self._config.update(config)

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


def config_dict_to_namelist(config_dict, namelist_filename):
    f90nml.write(config_dict, namelist_filename)


def config_dict_from_namelist(namelist_filename):
    try:
        return_dict = f90nml.read(namelist_filename)
    except FileNotFoundError:
        raise InvalidFileError(f'namelist {namelist_filename} does not exist')
    return return_dict


def config_dict_from_directory(dirname):
    return config_dict_from_namelist(os.path.join(dirname, 'input.nml'))


class ForcingData(object):

    def __init__(self):
        raise NotImplementedError()

    @classmethod
    def from_directory(cls, dirname):
        pass

    @classmethod
    def from_config(cls, config):
        pass

    def link(self, target_directory):
        pass
