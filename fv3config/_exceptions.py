class DataMissingError(FileNotFoundError):
    """Raised when expected cached data is not present."""
    pass


class InvalidFileError(FileNotFoundError):
    """Raised when a specified file is invalid, either non-existent or not as expected."""
    pass


class ConfigError(ValueError):
    pass
