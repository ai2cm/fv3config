import logging
from typing import Sequence, Optional, Union
import dataclasses
from datetime import datetime, timedelta
import re
import sys

from .._exceptions import ConfigError

logger = logging.getLogger("fv3config")


@dataclasses.dataclass
class DiagTableField:
    """Object representing a field of a diagnostics file."""

    module_name: str
    field_name: str
    output_name: str
    reduction_method: Optional[str] = "none"
    time_sampling: Optional[str] = "all"
    regional_section: Optional[str] = "none"
    packing: Optional[int] = 2


@dataclasses.dataclass
class DiagTableFile:
    """Object representing a diagnostics file."""

    name: str
    frequency: int
    frequency_units: str
    fields: Sequence[DiagTableField]
    file_format: Optional[int] = 1
    time_axis_units: Optional[str] = "hours"
    time_axis_name: Optional[str] = "time"


class DiagTable:
    def __init__(
        self, name: str, base_time: datetime, files: Sequence[DiagTableFile],
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
            files: sequence of DiagTableFile's defining the diagnostics to be output.
        """
        if " " in name:
            raise ConfigError(f"Name for diag_table cannot have spaces. Got '{name}''.")
        self.name = name
        self.base_time = base_time
        self.files = files

    def __repr__(self):
        """Representation of diag_table expected by the Fortran model."""
        lines = []
        lines.append(self.name)
        lines.append(self._time_to_str(self.base_time))
        lines.append("")

        for file_ in self.files:
            lines.append(self._file_repr(file_))

        lines.append("")
        for file_ in self.files:
            for field in file_.fields:
                lines.append(self._field_repr(field, file_.name))
            lines.append("")

        return "\n".join(lines)

    def _file_repr(self, file_: DiagTableFile) -> str:
        tokens = (
            file_.name,
            file_.frequency,
            file_.frequency_units,
            file_.file_format,
            file_.time_axis_units,
            file_.time_axis_name,
        )
        return ", ".join(self._token_to_str(t) for t in tokens)

    def _field_repr(self, field: DiagTableField, file_name: str) -> str:
        tokens = (
            field.module_name,
            field.field_name,
            field.output_name,
            file_name,
            field.time_sampling,
            field.reduction_method,
            field.regional_section,
            field.packing,
        )
        return ", ".join(self._token_to_str(t) for t in tokens)

    @staticmethod
    def _time_to_str(time: datetime) -> str:
        times = [time.year, time.month, time.day, time.hour, time.minute, time.second]
        return " ".join([str(t) for t in times])

    @staticmethod
    def _str_to_time(line: str) -> datetime:
        time_sequence = [int(d) for d in re.findall(r"\d+", line)]
        return datetime(*time_sequence)

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
        token_strings = line.replace(" ", "").strip(",").split(",")
        return list(map(DiagTable._str_to_token, token_strings))

    @classmethod
    def from_str(cls, diag_table: str):
        """Initialize DiagTable class from Fortran string representation."""
        lines = diag_table.split("\n")
        lines = [line for line in lines if line and line[0] != "#"]
        parsed_lines = list(map(cls._parse_line, lines[2:]))

        file_lines = []
        field_lines = {}

        for tokens in parsed_lines:
            if len(tokens) == 6:
                # line corresponds to definition of a file
                file_name = tokens[0]
                file_lines.append(tokens)
                field_lines[file_name] = []
            elif len(tokens) == 8:
                # line corresponds to definition of a field
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

        files = []
        for file_tokens in file_lines:
            file_name = file_tokens[0]
            fields = []
            for field_tokens in field_lines[file_name]:
                fields.append(
                    DiagTableField(
                        module_name=field_tokens[0],
                        field_name=field_tokens[1],
                        output_name=field_tokens[2],
                        time_sampling=field_tokens[4],
                        reduction_method=field_tokens[5],
                        regional_section=field_tokens[6],
                        packing=field_tokens[7],
                    )
                )
            files.append(
                DiagTableFile(
                    name=file_name,
                    frequency=file_tokens[1],
                    frequency_units=file_tokens[2],
                    fields=fields,
                    file_format=file_tokens[3],
                    time_axis_units=file_tokens[4],
                    time_axis_name=file_tokens[5],
                )
            )
        name = lines[0]
        base_time = cls._str_to_time(lines[1])
        return cls(name, base_time, files)


if __name__ == "__main__":
    path = sys.argv[1]

    with open(path) as f:
        input_ = f.read()

    diag_table = DiagTable.from_str(input_)

    print(diag_table)
