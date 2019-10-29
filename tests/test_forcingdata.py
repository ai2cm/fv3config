import unittest
import os
import shutil
from fv3config import (
    get_default_config, ConfigError,
    write_run_directory
)
from fv3config._datastore import (
    get_base_forcing_directory, get_orographic_forcing_directory,
    link_directory, get_initial_conditions_directory, ensure_data_is_downloaded
)

test_directory = os.path.dirname(os.path.realpath(__file__))

required_run_directory_subdirectories = ['INPUT', 'RESTART']

required_base_forcing_filenames = [
    f'co2historicaldata_{year}.txt' for year in range(2010, 2017)
] + [
    'sfc_emissivity_idx.txt',
    'solarconstant_noaa_an.txt',
    'aerosol.dat',
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
    f'INPUT/oro_data.tile{tile}.nc' for tile in range(1, 7)
]

required_default_initial_conditions_filenames = [
    'INPUT/gfs_ctrl.nc'
] + [
    f'INPUT/gfs_data.tile{n}.nc' for n in range(1, 7)
] + [
    f'INPUT/sfc_data.tile{n}.nc' for n in range(1, 7)
]

required_restart_initial_conditions_filenames = [
    'INPUT/coupler.res'
] + [
    f'INPUT/fv_core.res.tile{n}.nc' for n in range(1, 7)
] + [
    f'INPUT/fv_srf_wnd.res.tile{n}.nc' for n in range(1, 7)
] + [
    f'INPUT/fv_tracer.res.tile{n}.nc' for n in range(1, 7)
] + [
    f'INPUT/phy_data.tile{n}.nc' for n in range(1, 7)
] + [
    f'INPUT/sfc_data.tile{n}.nc' for n in range(1, 7)
]

additional_required_filenames = [
    'data_table',
    'diag_table',
    'field_table',
    'input.nml',
]

required_config_keys = [
    'namelist',
    'diag_table',
    'data_table',
    'forcing',
    'experiment_name',
    'initial_conditions'
]


class RunDirectory(object):

    def __init__(self, directory_path):
        os.mkdir(directory_path)
        os.mkdir(os.path.join(directory_path, 'INPUT'))
        os.mkdir(os.path.join(directory_path, 'RESTART'))
        self.directory_path = directory_path

    def cleanup(self):
        shutil.rmtree(self.directory_path)


class ForcingTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        ensure_data_is_downloaded()
        super(ForcingTests, self).__init__(*args, **kwargs)

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
        config = get_default_config()
        forcing_dir = get_base_forcing_directory(config)
        self.assertTrue(os.path.isdir(forcing_dir))
        link_directory(forcing_dir, rundir)
        for filename in required_base_forcing_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_link_default_orographic_forcing_directory(self):
        rundir = self.make_run_directory('test_rundir')
        config = get_default_config()
        orographic_forcing_dir = get_orographic_forcing_directory(config)
        self.assertTrue(os.path.isdir(orographic_forcing_dir))
        link_directory(orographic_forcing_dir, os.path.join(rundir, 'INPUT'))
        for filename in required_orographic_forcing_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_zero_resolution_orographic_forcing_directory(self):
        config = {
            'namelist': {
                'fv_core_nml': {
                    'npx': 0,
                    'npy': 0,
                }
            }
        }
        with self.assertRaises(ConfigError):
            get_orographic_forcing_directory(config)

    def test_negative_resolution_orographic_forcing_directory(self):
        config = {
            'namelist': {
                'fv_core_nml': {
                    'npx': -1,
                    'npy': -1,
                }
            }
        }
        with self.assertRaises(ConfigError):
            get_orographic_forcing_directory(config)

    def test_link_default_initial_conditions_directory(self):
        rundir = self.make_run_directory('test_rundir')
        config = get_default_config()
        initial_conditions_dir = get_initial_conditions_directory(config)
        self.assertTrue(os.path.isdir(initial_conditions_dir))
        link_directory(initial_conditions_dir, os.path.join(rundir, 'INPUT'))
        for filename in required_default_initial_conditions_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_link_gfs_initial_conditions_directory(self):
        rundir = self.make_run_directory('test_rundir')
        config = get_default_config()
        config['initial_conditions'] = 'gfs_example'
        initial_conditions_dir = get_initial_conditions_directory(config)
        self.assertTrue(os.path.isdir(initial_conditions_dir))
        link_directory(initial_conditions_dir, os.path.join(rundir, 'INPUT'))
        for filename in required_default_initial_conditions_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_link_restart_initial_conditions_directory(self):
        rundir = self.make_run_directory('test_rundir')
        config = get_default_config()
        config['initial_conditions'] = 'restart_example'
        initial_conditions_dir = get_initial_conditions_directory(config)
        self.assertTrue(os.path.isdir(initial_conditions_dir))
        link_directory(initial_conditions_dir, os.path.join(rundir, 'INPUT'))
        for filename in required_restart_initial_conditions_filenames:
            full_filename = os.path.join(rundir, filename)
            self.assertTrue(os.path.isfile(full_filename), msg=full_filename)

    def test_get_specified_initial_conditions_directory(self):
        source_rundir = self.make_run_directory('source_rundir')
        config = get_default_config()
        config['initial_conditions'] = source_rundir
        dirname = get_initial_conditions_directory(config)
        self.assertEqual(dirname, source_rundir)

    def test_get_bad_initial_conditions_directory(self):
        source_rundir = '/not/a/real/directory'
        config = get_default_config()
        config['initial_conditions'] = source_rundir
        with self.assertRaises(ConfigError):
            get_initial_conditions_directory(config)

    def test_get_specified_forcing_directory(self):
        source_rundir = self.make_run_directory('source_rundir')
        config = get_default_config()
        config['forcing'] = source_rundir
        dirname = get_base_forcing_directory(config)
        self.assertEqual(dirname, source_rundir)

    def test_get_bad_forcing_directory(self):
        source_rundir = '/not/a/real/directory'
        config = get_default_config()
        config['forcing'] = source_rundir
        with self.assertRaises(ConfigError):
            get_base_forcing_directory(config)

    def test_write_default_run_directory(self):
        rundir = self.make_run_directory('test_rundir')
        config = get_default_config()
        write_run_directory(config, rundir)
        missing_subdirectories = []
        for subdirectory in required_run_directory_subdirectories:
            full_path = os.path.join(rundir, subdirectory)
            if not os.path.isdir(full_path):
                missing_subdirectories.append(full_path)
        missing_filenames = []
        for filename in (
                required_default_initial_conditions_filenames +
                required_base_forcing_filenames +
                required_orographic_forcing_filenames +
                additional_required_filenames):
            full_filename = os.path.join(rundir, filename)
            if not os.path.isfile(full_filename):
                missing_filenames.append(full_filename)
        self.assertTrue(len(missing_filenames) == 0, missing_filenames)

    def test_restart_directory_exists_and_empty(self):
        rundir = self.make_run_directory('test_rundir')
        restart_directory = os.path.join(rundir, 'RESTART')
        config = get_default_config()
        write_run_directory(config, rundir)
        self.assertTrue(os.path.isdir(restart_directory))
        self.assertEqual(len(os.listdir(restart_directory)), 0)

    def test_default_config_has_required_keys(self):
        config = get_default_config()
        self.assertTrue(set(required_config_keys) <= set(config.keys()))


if __name__ == '__main__':
    unittest.main()
