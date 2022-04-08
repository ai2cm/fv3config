from fv3config.filesystem import _get_protocol_prefix, _Location


def test__Location_get_protocol():
    # copilot generated all of these cases magically!
    assert _Location("gs://my-bucket/my_filename.txt").get_protocol() == "gs"
    assert _Location("http://www.mysite.com/dir/file.nc").get_protocol() == "http"
    assert _Location("memory:///some/path").get_protocol() == "memory"
    assert _Location("file:///some/path").get_protocol() == "file"
    assert _Location("/some/path").get_protocol() == "file"
    assert _Location("some/path").get_protocol() == "file"
    assert _Location("").get_protocol() == "file"


def test__get_protocol_prefix():
    # copilot generated all of these magically!
    assert _get_protocol_prefix("gs://my-bucket/my_filename.txt") == "gs://"
    assert _get_protocol_prefix("http://www.mysite.com/dir/file.nc") == "http://"
    assert _get_protocol_prefix("memory:///some/path") == "memory://"
    assert _get_protocol_prefix("file:///some/path") == "file://"
    assert _get_protocol_prefix("/some/path") == ""
    assert _get_protocol_prefix("some/path") == ""
    assert _get_protocol_prefix("") == ""
