import os
import datastore

class ForcingData(object):

    # files in the data directory to ignore if present, linked otherwise
    exclude_root_filenames = []
    # files in subdirectories to link if present, ignored otherwise
    include_subdirectory_filenames = []

    def __init__(self):
        return ForcingData.from_directory(datastore.default_forcing_directory)

    @classmethod
    def from_directory(cls, dirname):
        if data_directory is None:
            data_directory = datastore.default_forcing_directory
        self.data_directory = data_directory

    @classmethod
    def from_config(cls, config):
        raise NotImplementedError()

    def link(self, target_directory):
        for filename in os.listdir(self.data_directory):
            source_path = os.path.join(self.data_directory, filename)
            target_path = os.path.join(target_directory, filename)
            if os.path.isfile(target_path):
                os.remove(target_path)
            os.symlink(source_path, target_path)
