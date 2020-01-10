import os
import appdirs

if "FV3CONFIG_CACHE_DIR" in os.environ:
    USER_CACHE_DIR = os.environ["FV3CONFIG_CACHE_DIR"]
else:
    USER_CACHE_DIR = appdirs.user_cache_dir("fv3gfs", "vulcan")
    os.makedirs(USER_CACHE_DIR, exist_ok=True)
CACHE_PREFIX = "fv3config-cache"


def set_cache_dir(parent_dirname):
    if not os.path.isdir(parent_dirname):
        raise ValueError(f"{parent_dirname} does not exist")
    elif not os.path.isdir(os.path.join(parent_dirname, CACHE_PREFIX)):
        os.mkdir(os.path.join(parent_dirname, CACHE_PREFIX))
    global USER_CACHE_DIR
    USER_CACHE_DIR = parent_dirname


def get_cache_dir():
    return USER_CACHE_DIR


def get_internal_cache_dir():
    return os.path.join(USER_CACHE_DIR, CACHE_PREFIX)
