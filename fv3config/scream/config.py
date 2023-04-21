import dataclasses
from typing import Any, Dict, Union
import fv3config
import os
import dacite


def gather_output_yaml(output_yaml, target_directory):
    local_output_yaml = []
    if isinstance(output_yaml, list):
        for output in output_yaml:
            fv3config.filesystem.get_file(
                output, os.path.join(target_directory, os.path.basename(output))
            )
            local_output_yaml.append(
                os.path.join(target_directory, os.path.basename(output))
            )
    elif isinstance(output_yaml, str):
        fv3config.filesystem.get_file(
            output_yaml, os.path.join(target_directory, os.path.basename(output_yaml))
        )
        local_output_yaml.append(
            os.path.join(target_directory, os.path.basename(output_yaml))
        )
    else:
        assert TypeError("output_yaml must be a list of string or a string")
    return local_output_yaml


@dataclasses.dataclass
class ScreamConfig:
    output_yaml: Union[str, list] = "gs://vcm-scream/config/output/default.yaml"
    initial_conditions_type: str = "local"
    create_newcase: bool = True
    case_setup: bool = True
    case_build: bool = True
    case_submit: bool = False
    upload_to_cloud: bool = False
    upload_to_cloud_path: str = "gs://vcm-ml-scratch/scream/scream_test"
    number_of_processers: int = 16
    CASE_ROOT: str = ""
    CASE_NAME: str = "scream_test"
    COMPSET: str = "F2010-SCREAMv1"
    RESOLUTION: str = "ne30pg2_ne30pg2"
    ATM_NCPL: int = 48
    STOP_OPTION: str = "nhours"
    STOP_N: int = 1
    REST_OPTION: str = "nhours"
    REST_N: int = 1
    HIST_OPTION: str = "ndays"
    HIST_N: int = 1
    RUN_STARTDATE: str = "2010-01-01"
    MODEL_START_TYPE: str = "initial"
    OLD_EXECUTABLE: str = ""

    def __post__init__(self):
        # TODO: we may want to support other option such as initial_conditions_type = "cloud"
        # in which case we need to download the initial conditions files
        assert (
            self.initial_conditions_type == "local"
        ), "at the moment, initial_conditions_type must be local, \
            meaning the input files were already on disk or \
            mounted through persistentVolume"

    def resolve_output_yaml(self, target_directory: str):
        if not fv3config.filesystem.is_local_path(self.output_yaml):
            self.output_yaml = gather_output_yaml(self.output_yaml, target_directory)

    @classmethod
    def from_dict(cls, kwargs: Dict[str, Any]) -> "ScreamConfig":
        return dacite.from_dict(
            data_class=cls, data=kwargs, config=dacite.Config(strict=True)
        )
