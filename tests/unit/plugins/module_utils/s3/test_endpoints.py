# -*- coding: utf-8 -*-
#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import s3

mod_urlparse = "ansible_collections.amazon.aws.plugins.module_utils.s3.urlparse"


class UrlInfo:
    def __init__(self, scheme=None, hostname=None, port=None):
        self.hostname = hostname
        self.scheme = scheme
        self.port = port


@patch(mod_urlparse)
def test_is_fakes3_with_none_arg(m_urlparse):
    m_urlparse.side_effect = SystemExit(1)
    result = s3.is_fakes3(None)
    assert not result
    m_urlparse.assert_not_called()


@pytest.mark.parametrize(
    "url,scheme,result",
    [
        ("https://test-s3.amazon.com", "https", False),
        ("fakes3://test-s3.amazon.com", "fakes3", True),
        ("fakes3s://test-s3.amazon.com", "fakes3s", True),
    ],
)
@patch(mod_urlparse)
def test_is_fakes3(m_urlparse, url, scheme, result):
    m_urlparse.return_value = UrlInfo(scheme=scheme)
    assert result == s3.is_fakes3(url)
    m_urlparse.assert_called_with(url)


@pytest.mark.parametrize(
    "url,urlinfo,endpoint",
    [
        (
            "fakes3://test-s3.amazon.com",
            {"scheme": "fakes3", "hostname": "test-s3.amazon.com"},
            {"endpoint": "http://test-s3.amazon.com:80", "use_ssl": False},
        ),
        (
            "fakes3://test-s3.amazon.com:8080",
            {"scheme": "fakes3", "hostname": "test-s3.amazon.com", "port": 8080},
            {"endpoint": "http://test-s3.amazon.com:8080", "use_ssl": False},
        ),
        (
            "fakes3s://test-s3.amazon.com",
            {"scheme": "fakes3s", "hostname": "test-s3.amazon.com"},
            {"endpoint": "https://test-s3.amazon.com:443", "use_ssl": True},
        ),
        (
            "fakes3s://test-s3.amazon.com:9096",
            {"scheme": "fakes3s", "hostname": "test-s3.amazon.com", "port": 9096},
            {"endpoint": "https://test-s3.amazon.com:9096", "use_ssl": True},
        ),
    ],
)
@patch(mod_urlparse)
def test_parse_fakes3_endpoint(m_urlparse, url, urlinfo, endpoint):
    m_urlparse.return_value = UrlInfo(**urlinfo)
    result = s3.parse_fakes3_endpoint(url)
    assert endpoint == result
    m_urlparse.assert_called_with(url)


@pytest.mark.parametrize(
    "url,scheme,use_ssl",
    [
        ("https://test-s3-ceph.amazon.com", "https", True),
        ("http://test-s3-ceph.amazon.com", "http", False),
    ],
)
@patch(mod_urlparse)
def test_parse_ceph_endpoint(m_urlparse, url, scheme, use_ssl):
    m_urlparse.return_value = UrlInfo(scheme=scheme)
    result = s3.parse_ceph_endpoint(url)
    assert result == {"endpoint": url, "use_ssl": use_ssl}
    m_urlparse.assert_called_with(url)
