import unittest


class StateDataTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_from_empty_directory(self):
        pass

    def test_init_from_one_file_in_directory(self):
        pass

    def test_init_from_one_file_in_subdirectory(self):
        pass

    def test_init_from_realistic_directory(self):
        pass

    def test_init_from_default_config(self):
        pass

    def test_write_from_default_config(self):
        pass

    def test_write_from_same_io_config(self):
        """
        Test loading a folder and saving it to another directory using the same IO domain decomposition.
        """
        pass

    def test_write_from_different_io_config(self):
        """
        Test loading a folder and saving it to another directory using a new IO domain decomposition.
        """
        pass

    def test_write_to_same_directory_same_io_config(self):
        """
        Test loading a folder and calling write to the same folder when no changes are necessary.
        """
        pass

    def test_write_to_same_directory_different_io_config(self):
        """
        Test loading a folder and calling write to the same folder when there is a new IO domain
        decomposition and changes are necessary.
        """
        pass


if __name__ == '__main__':
    unittest.main()