class DataMissingError(FileNotFoundError):
    """Raised when expected cached data is not present."""
    pass


class InvalidFileError(FileNotFoundError):
    """Raised when a specified file is invalid, either non-existent or not as expected."""
    pass


class ConfigError(ValueError):
    pass


class DelayedImportError(object):

    def __init__(self, message):
        self.message = message

    def __getattr__(self):
        raise ImportError(self.message)


class DependencyError(Exception):
    """Raised when code tries to use an optional dependency that is not installed"""
    pass
