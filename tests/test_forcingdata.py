import unittest
from fv3config import (
    get_base_forcing_directory, get_orographic_forcing_directory, link_directory,
    get_default_config_dict, ConfigError
)
import os
import shutil

test_directory = os.path.dirname(os.path.realpath(__file__))

required_base_forcing_filenames = [
    f'co2historicaldata_{year}.txt' for year in range(2010, 2017)
] + [
    'sfc_emissivity_idx.txt',
    'solarconstant_noaa_an.txt',
    'aerosol.dat',
    'data_table',
    'INPUT/global_o3prdlos.f77'
] + [
    'grb/CFSR.SEAICE.1982.2012.monthly.clim.grb', 'grb/global_snoclim.1.875.grb',
    'grb/RTGSST.1982.2012.monthly.clim.grb', 'grb/global_snowfree_albedo.bosu.t1534.3072.1536.rg.grb',
    'grb/global_albedo4.1x1.grb', 'grb/global_soilmgldas.t1534.3072.1536.grb',
    'grb/global_glacier.2x2.grb', 'grb/global_soiltype.statsgo.t1534.3072.1536.rg.grb',
    'grb/global_maxice.2x2.grb', 'grb/global_tg3clim.2.6x1.5.grb',
    'grb/global_mxsnoalb.uariz.t1534.3072.1536.rg.grb', 'grb/global_vegfrac.0.144.decpercent.grb',
    'grb/global_shdmax.0.144x0.144.grb', 'grb/global_vegtype.igbp.t1534.3072.1536.rg.grb',
    'grb/global_shdmin.0.144x0.144.grb', 'grb/seaice_newland.grb',
    'grb/global_slope.1x1.grb',
]

required_orographic_forcing_filenames = [
    f'oro_data.tile{tile}.nc' for tile in range(1, 7)
]

class RunDirectory(object):

    def __init__(self, directory_path):
        os.mkdir(directory_path)
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

    def test_link_default_base_forcing_directory(self):
        rundir = self.make_run_directory('test_rundir')
        forcing_dir = get_base_forcing_directory()
        self.assertTrue(os.path.isdir(forcing_dir))
        link_directory(forcing_dir, rundir)
        for filename in required_base_forcing_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_invalid_base_forcing_option(self):
        with self.assertRaises(ConfigError):
            get_base_forcing_directory('invalid_option')

    def test_link_default_orographic_forcing_directory(self):
        rundir = self.make_run_directory('test_rundir')
        config = get_default_config_dict()
        orographic_forcing_dir = get_orographic_forcing_directory(config)
        self.assertTrue(os.path.isdir(orographic_forcing_dir))
        link_directory(orographic_forcing_dir, rundir)
        for filename in required_orographic_forcing_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_zero_resolution_orographic_forcing_directory(self):
        config = {
            'fv_core_nml': {
                'npx': 0,
                'npy': 0,
            }
        }
        with self.assertRaises(ConfigError):
            get_orographic_forcing_directory(config)

    def test_negative_resolution_orographic_forcing_directory(self):
        config = {
            'fv_core_nml': {
                'npx': -1,
                'npy': -1,
            }
        }
        with self.assertRaises(ConfigError):
            get_orographic_forcing_directory(config)


if __name__ == '__main__':
    unittest.main()
