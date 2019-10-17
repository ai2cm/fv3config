# -*- coding: utf-8 -*-

"""Main module."""
import os
import f90nml


class GFSData(object):

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


class RestartData(object):

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

