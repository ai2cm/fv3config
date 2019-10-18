import unittest
from fv3config import ForcingData
import os
import shutil

test_directory = os.path.dirname(os.path.realpath(__file__))

required_forcing_filenames = [
    f'co2historicaldata_{year}' for year in range(2010, 2017)
] + [
    'sfc_emissivity_idx.txt',
    'solarconstant_noaa_an.txt',
    'aerosol.dat',
    'data_table',
    'INPUT/global_o3prdlos.f77'
] + [
    f'INPUT/oro_data.tile{n}.nc' for n in range(1, 7)
] + [
    'grb/CFSR_SEAICE.1982.2012.monthly.clim.grb',
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

    def test_init_from_empty_directory(self):
        rundir = self.make_run_directory('test_rundir')
        forcing = ForcingData(rundir)
        self.assertEqual(forcing.data_directory, rundir)

    def test_get_forcing_directory_for_empty_config(self):
        rundir = self.make_run_directory('test_rundir')
        forcing = ForcingData.from_config({})
        forcing.link(rundir)
        for filename in required_forcing_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)


    def test_init_from_one_file_in_subdirectory(self):
        pass

    def test_init_from_realistic_directory(self):
        pass

    def test_link_from_one_file_in_directory(self):
        pass

    def test_link_from_one_file_in_subdirectory(self):
        pass

    def test_link_from_realistic_directory(self):
        pass

    def test_init_from_default_config(self):
        pass

    def test_link_from_default_config(self):
        pass


if __name__ == '__main__':
    unittest.main()
