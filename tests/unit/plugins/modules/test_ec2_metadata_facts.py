# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import gzip
import io
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_metadata_facts"


class FailJson(Exception):
    pass


@pytest.fixture()
def ec2_instance():
    module = MagicMock()
    return ec2_metadata_facts.Ec2Metadata(module)


@patch(module_name + ".fetch_url")
def test__fetch_401(m_fetch_url, ec2_instance):
    ec2_instance.module.fail_json.side_effect = FailJson()
    m_fetch_url.return_value = (None, {"status": 401, "msg": "Oops"})
    with pytest.raises(FailJson):
        ec2_instance._fetch("http://169.254.169.254/latest/meta-data/")


@patch(module_name + ".fetch_url")
def test__fetch_200(m_fetch_url, ec2_instance):
    m_fetch_url.return_value = (io.StringIO("my-value"), {"status": 200})
    assert ec2_instance._fetch("http://169.254.169.254/latest/meta-data/ami-id") == "my-value"

    m_fetch_url.return_value = (io.StringIO("1"), {"status": 200})
    assert ec2_instance._fetch("http://169.254.169.254/latest/meta-data/ami-id") == "1"


@patch(module_name + ".fetch_url")
def test_fetch(m_fetch_url, ec2_instance):
    raw_list = "ami-id\n"
    m_fetch_url.side_effect = [
        (io.StringIO(raw_list), {"status": 200}),
        (io.StringIO("my-value"), {"status": 200}),
    ]
    ec2_instance.fetch("http://169.254.169.254/latest/meta-data/")
    assert ec2_instance._data == {"http://169.254.169.254/latest/meta-data/ami-id": "my-value"}


@patch(module_name + ".fetch_url")
def test_fetch_recusive(m_fetch_url, ec2_instance):
    raw_list = "whatever/\n"
    m_fetch_url.side_effect = [
        (io.StringIO(raw_list), {"status": 200}),
        (io.StringIO("my-key"), {"status": 200}),
        (io.StringIO("my-value"), {"status": 200}),
    ]
    ec2_instance.fetch("http://169.254.169.254/latest/meta-data/")
    assert ec2_instance._data == {"http://169.254.169.254/latest/meta-data/whatever/my-key": "my-value"}


@patch(module_name + ".fetch_url")
def test__fetch_user_data_compressed(m_fetch_url, ec2_instance):
    user_data = b"""Content-Type: multipart/mixed; boundary="MIMEBOUNDARY"
MIME-Version: 1.0

--MIMEBOUNDARY
Content-Transfer-Encoding: 7bit
Content-Type: text/cloud-config
Mime-Version: 1.0

packages: ['httpie']

--MIMEBOUNDARY--
"""

    m_fetch_url.return_value = (io.BytesIO(gzip.compress(user_data)), {"status": 200})
    assert ec2_instance._fetch("http://169.254.169.254/latest/user-data") == user_data.decode("utf-8")


@patch(module_name + ".fetch_url")
def test__fetch_user_data_plain(m_fetch_url, ec2_instance):
    user_data = b"""Content-Type: multipart/mixed; boundary="MIMEBOUNDARY"
MIME-Version: 1.0

--MIMEBOUNDARY
Content-Transfer-Encoding: 7bit
Content-Type: text/cloud-config
Mime-Version: 1.0

packages: ['httpie']

--MIMEBOUNDARY--
"""

    m_fetch_url.return_value = (io.BytesIO(user_data), {"status": 200})
    assert ec2_instance._fetch("http://169.254.169.254/latest/user-data") == user_data.decode("utf-8")
