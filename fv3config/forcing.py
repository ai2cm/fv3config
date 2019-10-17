import os
import datastore

def link_directory(source_path, target_path):
    for filename in os.listdir(source_path):
        source_item = os.path.join(source_path, filename)
        target_item = os.path.join(target_path, filename)
        if os.path.isfile(source_item):
            if os.path.isfile(target_path):
                os.remove(target_path)
            os.symlink(source_path, target_path)
        elif os.path.isdir(source_item):
            link_directory(source_item, target_item)


def get_forcing_directory_for_config(config):
    pass
