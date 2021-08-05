# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# Magic...  Incorrectly identified by pylint as unused
from ansible_collections.amazon.aws.tests.unit.utils.amazon_placebo_fixtures import placeboify  # pylint: disable=unused-import
from ansible_collections.amazon.aws.tests.unit.compat.mock import patch

from ansible_collections.amazon.aws.plugins.modules import ec2_vpc_dhcp_option as dhcp_module
from ansible_collections.amazon.aws.tests.unit.plugins.modules.utils import ModuleTestCase

test_module_params = {'domain_name': 'us-west-2.compute.internal',
                      'dns_servers': ['AmazonProvidedDNS'],
                      'ntp_servers': ['10.10.2.3', '10.10.4.5'],
                      'netbios_name_servers': ['10.20.2.3', '10.20.4.5'],
                      'netbios_node_type': 2}

test_create_config = [{'Key': 'domain-name', 'Values': [{'Value': 'us-west-2.compute.internal'}]},
                      {'Key': 'domain-name-servers', 'Values': [{'Value': 'AmazonProvidedDNS'}]},
                      {'Key': 'ntp-servers', 'Values': [{'Value': '10.10.2.3'}, {'Value': '10.10.4.5'}]},
                      {'Key': 'netbios-name-servers', 'Values': [{'Value': '10.20.2.3'}, {'Value': '10.20.4.5'}]},
                      {'Key': 'netbios-node-type', 'Values': 2}]


test_create_option_set = [{'Key': 'domain-name', 'Values': ['us-west-2.compute.internal']},
                          {'Key': 'domain-name-servers', 'Values': ['AmazonProvidedDNS']},
                          {'Key': 'ntp-servers', 'Values': ['10.10.2.3', '10.10.4.5']},
                          {'Key': 'netbios-name-servers', 'Values': ['10.20.2.3', '10.20.4.5']},
                          {'Key': 'netbios-node-type', 'Values': ['2']}]

test_normalize_config = {'domain-name': ['us-west-2.compute.internal'],
                         'domain-name-servers': ['AmazonProvidedDNS'],
                         'ntp-servers': ['10.10.2.3', '10.10.4.5'],
                         'netbios-name-servers': ['10.20.2.3', '10.20.4.5'],
                         'netbios-node-type': '2'
                         }


class FakeModule(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('FAIL')

    def fail_json_aws(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('FAIL')

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('EXIT')


@patch.object(dhcp_module.AnsibleAWSModule, 'client')
class TestDhcpModule(ModuleTestCase):

    def test_create_dhcp_config(self, client_mock):
        self.params = test_module_params
        result = dhcp_module.create_dhcp_config(self)

        assert result == test_create_config

    def test_create_dhcp_option_set(self, client_mock):
        self.check_mode = False
        dhcp_module.create_dhcp_option_set(client_mock, self, test_create_config)
        client_mock.create_dhcp_options.assert_called_once_with(DhcpConfigurations=test_create_option_set, aws_retry=True)

    def test_normalize_config(self, client_mock):
        result = dhcp_module.normalize_ec2_vpc_dhcp_config(test_create_config)

        print(result)
        print(test_normalize_config)
        assert result == test_normalize_config
