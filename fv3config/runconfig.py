from .config import default_config_dict, ConfigDict, config_dict_to_namelist
from .forcing import get_forcing_directory_for_config, link_directory, GFSData, RestartData

class RunConfig(object):

    def __init__(self, input_data=None, forcing_dir=None, config=None):
        if config is None:
            self._config = default_config_dict()
        else:
            self._config = config
        self._input_data = input_data or GFSData.from_config(self._config)
        self._forcing_directory = forcing_dir or get_forcing_directory_for_config(self._config)

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
        config_dict_to_namelist(self._config, os.path.join(target_directory, 'input.nml'))
