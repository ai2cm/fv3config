import unittest
from fv3config import RunConfig


class MockStateData(object):

    def write(self, target_directory, config):
        pass


class MockForcingData(object):

    def link(self, target_directory):
        pass


class RunConfigTests(unittest.TestCase):

    def setUp(self):
        self.input_data = MockStateData()
        self.forcing_data = MockForcingData()

    def tearDown(self):
        self.input_data = None
        self.forcing_data = None

    def test_init_from_defaults(self):
        run = RunConfig()
        self.assertTrue(len(run.config) > 0)

    def test_init_from_realistic_directory(self):
        pass

    def test_init_from_mock(self):
        run = RunConfig(input_data=self.input_data, forcing_data=self.forcing_data)
        self.assertTrue(len(run.config) > 0)

    def test_write_defaults_to_new_directory(self):
        pass

    def test_write_defaults_to_empty_directory(self):
        pass

    def test_write_from_directory_to_empty_directory(self):
        pass

    def test_write_from_mock_to_empty_directory(self):
        pass

    def test_write_from_directory_to_existing_run_directory(self):
        pass

    def test_write_from_directory_to_directory_with_non_run_files(self):
        pass  # does it delete those files? should it?

    def test_write_restart_data_to_input_folder(self):
        pass

    def test_input_setter_replaces_input_from_directory(self):
        pass

    def test_config_setter_replaces_default_config(self):
        pass

    def test_editing_runconfig_with_default_config_keeps_defaults_the_same(self):
        """We want to make sure we can't change the default config by editing run.config"""
        pass


if __name__ == '__main__':
    unittest.main()