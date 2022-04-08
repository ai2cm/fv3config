from .mocks import MockGCSFileSystem


def test_mock_gscfs():
    fs = MockGCSFileSystem()
    fs.mkdir("a/b/c")

    for dir_ in ["gs://a", "gs://a/b", "gs://a/b/c"]:
        assert fs.exists(dir_)


def test_mock_gcsfs__strip_protocol():
    fs = MockGCSFileSystem()
    assert "a/long/path" == fs._strip_protocol("gs://a/long/path")
