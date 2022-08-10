# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six.moves.urllib.parse import urlparse

from ansible_collections.amazon.aws.plugins.modules import s3_object


class TestUrlparse():

    def test_urlparse(self):
        actual = urlparse("http://test.com/here")
        assert actual.scheme == "http"
        assert actual.netloc == "test.com"
        assert actual.path == "/here"

    def test_is_fakes3(self):
        actual = s3_object.is_fakes3("fakes3://bla.blubb")
        assert actual is True

    def test_get_s3_connection(self):
        aws_connect_kwargs = dict(aws_access_key_id="access_key",
                                  aws_secret_access_key="secret_key")
        location = None
        rgw = True
        s3_url = "http://bla.blubb"
        actual = s3_object.get_s3_connection(None, aws_connect_kwargs, location, rgw, s3_url)
        assert "bla.blubb" in str(actual._endpoint)
