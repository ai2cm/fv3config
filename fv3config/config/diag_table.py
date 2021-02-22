import logging
from typing import Sequence, Union, Tuple, Mapping
import dataclasses
import datetime
from enum import Enum
import re

import dacite

from .._exceptions import ConfigError

logger = logging.getLogger("fv3config")
NUMBER_OF_TOKENS_ON_FILE_LINES = 6
NUMBER_OF_TOKENS_ON_FIELD_LINES = 8


class Packing(Enum):
    DOUBLE_PRECISION = 1
    SINGLE_PRECISION = 2


class FileFormat(Enum):
    NETCDF = 1


@dataclasses.dataclass
class DiagFieldConfig:
    """Object representing configuration for a field of a diagnostics file.
    
    Args:
        module_name: Name of Fortran module containing diagnostic.
        field_name: Name of diagnostic within Fortran code.
        output_name: Name of diagnostic to use in output NetCDF.
        time_sampling: Always set to 'all'.
        reduction_method: One of 'none', 'average', 'min', 'max'.
        regional_section: 'none' or region specification.
        packing: precision for output data.
    """

    module_name: str
    field_name: str
    output_name: str
    time_sampling: str = "all"
    reduction_method: str = "none"
    regional_section: str = "none"
    packing: Packing = Packing.SINGLE_PRECISION


@dataclasses.dataclass
class DiagFileConfig:
    """Object representing a diagnostics file configuration.
    
    Args:
        name: Name to use for NetCDF files, not including '.tile?.nc'.
        frequency: Period between records in file.
        frequency_units: One of 'years', 'months', 'days', 'hours', 'minutes', 'seconds'
        field_configs: Sequence of DiagFieldConfigs defining fields to save.
        file_format: Always FileFormat.NETCDF.
        time_axis_units: Units for time coordinate in output files. One of 'years',
            'months', 'days', 'hours', 'minutes', 'seconds'.
        time_axis_name: Name for time coordinate in output files.
    """

    name: str
    frequency: int
    frequency_units: str
    field_configs: Sequence[DiagFieldConfig]
    file_format: FileFormat = FileFormat.NETCDF
    time_axis_units: str = "hours"
    time_axis_name: str = "time"


class DiagTable:
    def __init__(
        self,
        name: str,
        base_time: datetime.datetime,
        file_configs: Sequence[DiagFileConfig],
    ):
        """Representation of diag_table, which controls Fortran diagnostics manager.

        Note:
            This implementation is based on the diag_table specification described in
      https://data1.gfdl.noaa.gov/summer-school/Lectures/July16/03_Seth1_DiagManager.pdf
            The MOM6 documentation has a useful description as well:
            https://mom6.readthedocs.io/en/latest/api/generated/pages/Diagnostics.html.

        Args:
            name: label used as attribute in output diagnostic files. Cannot contain
                spaces.
            base_time: time to be used as reference for time coordinate units.
            file_configs: sequence of DiagFileConfig's defining the diagnostics to be
                output.
        """
        if " " in name:
            raise ConfigError(f"Name for diag_table cannot have spaces. Got '{name}'.")
        self.name = name
        self.base_time = base_time
        self.file_configs = file_configs

    def __repr__(self):
        """Representation of diag_table expected by the Fortran model."""
        lines = []
        lines.append(self.name)
        lines.append(self._time_to_str(self.base_time))
        lines.append("")

        for file_ in self.file_configs:
            lines.append(self._file_repr(file_))

        lines.append("")
        for file_ in self.file_configs:
            for field in file_.field_configs:
                lines.append(self._field_repr(field, file_.name))
            lines.append("")

        return "\n".join(lines)

    def asdict(self):
        return {
            "name": self.name,
            "base_time": self.base_time,
            "file_configs": [
                dataclasses.asdict(file_, dict_factory=self._dict_with_enums_factory)
                for file_ in self.file_configs
            ],
        }

    @staticmethod
    def _dict_with_enums_factory(data):
        def convert_value(obj):
            if isinstance(obj, Enum):
                return obj.value
            return obj

        return dict((k, convert_value(v)) for k, v in data)

    def _file_repr(self, file_: DiagFileConfig) -> str:
        tokens = (
            file_.name,
            file_.frequency,
            file_.frequency_units,
            file_.file_format.value,
            file_.time_axis_units,
            file_.time_axis_name,
        )
        return ", ".join(self._token_to_str(t) for t in tokens)

    def _field_repr(self, field: DiagFieldConfig, file_name: str) -> str:
        tokens = (
            field.module_name,
            field.field_name,
            field.output_name,
            file_name,
            field.time_sampling,
            field.reduction_method,
            field.regional_section,
            field.packing.value,
        )
        return ", ".join(self._token_to_str(t) for t in tokens)

    @staticmethod
    def _time_to_str(time: datetime.datetime) -> str:
        times = [time.year, time.month, time.day, time.hour, time.minute, time.second]
        return " ".join([str(t) for t in times])

    @staticmethod
    def _str_to_time(line: str) -> datetime.datetime:
        time_sequence = [int(d) for d in re.findall(r"\d+", line)]
        return datetime.datetime(*time_sequence)

    @staticmethod
    def _str_to_token(arg: str) -> Union[str, int]:
        if arg.startswith('"') and arg.endswith('"'):
            return arg.strip('"')
        elif arg.lower() == ".true.":
            # reduction_method can use '.true.' or '"average"' for same meaning
            return "average"
        elif arg.lower() == ".false.":
            # reduction_method can use '.false.' or '"none"' for same meaning
            return "none"
        else:
            return int(arg)

    @staticmethod
    def _token_to_str(token: Union[str, int]) -> str:
        if isinstance(token, str):
            return f'"{token}"'
        else:
            return str(token)

    @staticmethod
    def _parse_line(line: str) -> Sequence[Union[str, int]]:
        token_strings = line.replace(" ", "").split("#")[0].strip(",").split(",")
        return list(map(DiagTable._str_to_token, token_strings))

    @staticmethod
    def _organize_lines(
        parsed_lines: Sequence[str],
    ) -> Tuple[Sequence[str], Mapping[str, Sequence[str]]]:
        """Separate lines into 1) a sequence of lines describe files and 2) a mapping of
        file name to sequence of lines for all fields in that file."""
        file_lines = []
        field_lines = {}
        for tokens in parsed_lines:
            if len(tokens) == NUMBER_OF_TOKENS_ON_FILE_LINES:
                file_name = tokens[0]
                file_lines.append(tokens)
                field_lines[file_name] = []
            elif len(tokens) == NUMBER_OF_TOKENS_ON_FIELD_LINES:
                file_name = tokens[3]
                if file_name not in field_lines:
                    raise ConfigError(
                        "Files must be defined before they can be used by a field in "
                        f"diag_table. {file_name} has not been defined yet."
                    )
                field_lines[file_name].append(tokens)
            else:
                logger.warning(
                    f"Ignoring a line that could not be parsed in diag_table: {tokens}"
                )
        return file_lines, field_lines

    @staticmethod
    def _construct_configs_from_lines(
        file_lines, field_lines
    ) -> Sequence[DiagFileConfig]:
        file_configs = []
        for file_tokens in file_lines:
            file_name = file_tokens[0]
            field_configs = []
            for field_tokens in field_lines[file_name]:
                field_configs.append(
                    DiagFieldConfig(
                        module_name=field_tokens[0],
                        field_name=field_tokens[1],
                        output_name=field_tokens[2],
                        time_sampling=field_tokens[4],
                        reduction_method=field_tokens[5],
                        regional_section=field_tokens[6],
                        packing=Packing(field_tokens[7]),
                    )
                )
            file_configs.append(
                DiagFileConfig(
                    name=file_name,
                    frequency=file_tokens[1],
                    frequency_units=file_tokens[2],
                    field_configs=field_configs,
                    file_format=FileFormat(file_tokens[3]),
                    time_axis_units=file_tokens[4],
                    time_axis_name=file_tokens[5],
                )
            )
        return file_configs

    @classmethod
    def from_dict(cls, diag_table: dict):
        file_configs = [
            dacite.from_dict(DiagFileConfig, f, config=dacite.Config(cast=[Enum]))
            for f in diag_table["file_configs"]
        ]
        return cls(diag_table["name"], diag_table["base_time"], file_configs)

    @classmethod
    def from_str(cls, diag_table: str):
        """Initialize DiagTable class from Fortran string representation."""
        lines = diag_table.split("\n")
        lines = [line for line in lines if line and line.strip(" ")[0] != "#"]
        name = lines[0]
        base_time = cls._str_to_time(lines[1])
        parsed_lines = list(map(cls._parse_line, lines[2:]))
        file_lines, field_lines = cls._organize_lines(parsed_lines)
        file_configs = cls._construct_configs_from_lines(file_lines, field_lines)
        return cls(name, base_time, file_configs)
