import unittest
from fv3config import (
    get_default_config, ConfigError,
)
from fv3config.tables import (
    get_field_table_filename, get_diag_table_filename, get_data_table_filename,
    get_microphysics_name_from_config, get_current_date_from_coupler_res,
    get_current_date_from_config
)
import os
import shutil


test_directory = os.path.dirname(os.path.realpath(__file__))


valid_coupler_res = """    2        (Calendar: no_calendar=0, thirty_day_months=1, julian=2, gregorian=3, noleap=4)
  2016     8     1     0     0     0        Model start time:   year, month, day, hour, minute, second
  2016     8     3     0     0     0        Current model time: year, month, day, hour, minute, second
/
"""

valid_current_date = [2016, 8, 3, 0, 0, 0]

bad_coupler_res = """    2        (Calendar: no_calendar=0, thirty_day_months=1, julian=2, gregorian=3, noleap=4)
  2016     8     1     0     0     0        Model start time:   year, month, day, hour, minute, second
  2016     8  missing  0     0     0        Current model time: year, month, day, hour, minute, second
/
"""

class RunDirectory(object):

    def __init__(self, directory_path):
        os.mkdir(directory_path)
        os.mkdir(os.path.join(directory_path, 'INPUT'))
        os.mkdir(os.path.join(directory_path, 'RESTART'))
        self.directory_path = directory_path

    def cleanup(self):
        shutil.rmtree(self.directory_path)


class ForcingTests(unittest.TestCase):

    def setUp(self):
        self._run_directory_list = []

    def tearDown(self):
        for directory in self._run_directory_list:
            directory.cleanup()

    def make_run_directory(self, directory_name):
        full_path = os.path.join(test_directory, directory_name)
        self._run_directory_list.append(RunDirectory(full_path))
        return full_path

    def test_default_data_table_filename(self):
        config = get_default_config()
        filename = get_data_table_filename(config)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue('data_table' in filename)

    def test_default_diag_table_filename(self):
        config = get_default_config()
        filename = get_diag_table_filename(config)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue('diag_table' in filename)

    def test_default_field_table_filename(self):
        config = get_default_config()
        filename = get_field_table_filename(config)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue('field_table' in filename)

    def test_get_specified_data_table_filename(self):
        source_rundir = self.make_run_directory('source_rundir')
        data_table_filename = os.path.join(source_rundir, 'data_table')
        open(data_table_filename, 'w').close()
        config = get_default_config()
        config['data_table'] = data_table_filename
        filename = get_data_table_filename(config)
        self.assertEqual(filename, data_table_filename)

    def test_get_specified_diag_table_filename(self):
        source_rundir = self.make_run_directory('source_rundir')
        diag_table_filename = os.path.join(source_rundir, 'diag_table')
        open(diag_table_filename, 'w').close()
        config = get_default_config()
        config['diag_table'] = diag_table_filename
        filename = get_diag_table_filename(config)
        self.assertEqual(filename, diag_table_filename)

    def test_get_bad_field_table_filename(self):
        config = get_default_config()
        config['namelist']['gfs_physics_nml']['imp_physics'] = -1
        with self.assertRaises(NotImplementedError):
            get_field_table_filename(config)

    def test_get_bad_microphysics_name_from_config(self):
        config = get_default_config()
        config['namelist']['gfs_physics_nml']['imp_physics'] = -1
        with self.assertRaises(NotImplementedError):
            get_microphysics_name_from_config(config)

    def test_get_bad_diag_table_filename(self):
        diag_table_filename = '/not/a/path/diag_table'
        config = get_default_config()
        config['diag_table'] = diag_table_filename
        with self.assertRaises(ConfigError):
            get_diag_table_filename(config)

    def test_get_current_date_from_coupler_res(self):
        rundir = self.make_run_directory('test_rundir')
        coupler_res_filename = os.path.join(rundir, 'coupler.res')
        with open(coupler_res_filename, 'w') as f:
            f.write(valid_coupler_res)
        current_date = get_current_date_from_coupler_res(coupler_res_filename)
        self.assertEqual(current_date, valid_current_date)

    def test_get_current_date_from_bad_coupler_res(self):
        rundir = self.make_run_directory('test_rundir')
        coupler_res_filename = os.path.join(rundir, 'coupler.res')
        with open(coupler_res_filename, 'w') as f:
            f.write(bad_coupler_res)
        with self.assertRaises(ConfigError):
            get_current_date_from_coupler_res(coupler_res_filename)

    def test_get_current_date_from_config(self):
        config = get_default_config()
        config['namelist']['coupler_nml']['current_date'] = valid_current_date
        current_date = get_current_date_from_config(config)
        self.assertEqual(current_date, valid_current_date)


if __name__ == '__main__':
    unittest.main()
