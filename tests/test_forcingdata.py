import unittest
from fv3config import ForcingData


class RunDirectory(object):

    def __init__(self, directory_path):
        os.mkdir(directory_path)
        self.directory_path = directory_path

    def cleanup(self):
        shutil.rmtree(self.directory_path)

class ForcingDataTests(unittest.TestCase):

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

    def test_init_from_one_file_in_directory(self):
        pass

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
    unitest.main()
