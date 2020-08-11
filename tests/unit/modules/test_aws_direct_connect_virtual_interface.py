# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.tests.unit.utils.amazon_placebo_fixtures import placeboify, maybe_sleep
from ansible_collections.community.aws.plugins.modules import aws_direct_connect_virtual_interface


class FakeModule(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception("FAIL")

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs


def test_find_unique_vi_by_connection_id(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    vi_id = aws_direct_connect_virtual_interface.find_unique_vi(client, "dxcon-aaaaaaaa", None, None)
    assert vi_id == "dxvif-aaaaaaaa"


def test_find_unique_vi_by_vi_id(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    vi_id = aws_direct_connect_virtual_interface.find_unique_vi(client,
                                                                None,
                                                                "dxvif-aaaaaaaaa",
                                                                None)
    assert vi_id == "dxvif-aaaaaaaa"


def test_find_unique_vi_by_name(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    vi_id = aws_direct_connect_virtual_interface.find_unique_vi(client, None, None, "aaaaaaaa")
    assert vi_id == "dxvif-aaaaaaaa"


def test_find_unique_vi_returns_multiple(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    module = FakeModule(state="present",
                        id_to_associate="dxcon-aaaaaaaa",
                        public=False,
                        name=None)
    try:
        aws_direct_connect_virtual_interface.ensure_state(
            client,
            module
        )
    except Exception:
        assert "Multiple virtual interfaces were found" in module.exit_kwargs["msg"]


def test_find_unique_vi_returns_missing_for_vi_id(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    module = FakeModule(state="present",
                        id_to_associate=None,
                        public=False,
                        name=None,
                        virtual_interface_id="dxvif-aaaaaaaa")
    try:
        aws_direct_connect_virtual_interface.ensure_state(
            client,
            module
        )
    except Exception:
        assert "The virtual interface dxvif-aaaaaaaa does not exist" in module.exit_kwargs["msg"]


def test_construct_public_vi():
    module = FakeModule(state="present",
                        id_to_associate=None,
                        public=True,
                        name="aaaaaaaa",
                        vlan=1,
                        bgp_asn=123,
                        authentication_key="aaaa",
                        customer_address="169.254.0.1/30",
                        amazon_address="169.254.0.2/30",
                        address_type="ipv4",
                        cidr=["10.88.0.0/30"],
                        virtual_gateway_id="xxxx",
                        direct_connect_gateway_id="yyyy")
    vi = aws_direct_connect_virtual_interface.assemble_params_for_creating_vi(module.params)
    assert vi == {
        "virtualInterfaceName": "aaaaaaaa",
        "vlan": 1,
        "asn": 123,
        "authKey": "aaaa",
        "amazonAddress": "169.254.0.2/30",
        "customerAddress": "169.254.0.1/30",
        "addressFamily": "ipv4",
        "routeFilterPrefixes": [{"cidr": "10.88.0.0/30"}]
    }


def test_construct_private_vi_with_virtual_gateway_id():
    module = FakeModule(state="present",
                        id_to_associate=None,
                        public=False,
                        name="aaaaaaaa",
                        vlan=1,
                        bgp_asn=123,
                        authentication_key="aaaa",
                        customer_address="169.254.0.1/30",
                        amazon_address="169.254.0.2/30",
                        address_type="ipv4",
                        cidr=["10.88.0.0/30"],
                        virtual_gateway_id="xxxx",
                        direct_connect_gateway_id="yyyy")
    vi = aws_direct_connect_virtual_interface.assemble_params_for_creating_vi(module.params)
    assert vi == {
        "virtualInterfaceName": "aaaaaaaa",
        "vlan": 1,
        "asn": 123,
        "authKey": "aaaa",
        "amazonAddress": "169.254.0.2/30",
        "customerAddress": "169.254.0.1/30",
        "addressFamily": "ipv4",
        "virtualGatewayId": "xxxx"
    }


def test_construct_private_vi_with_direct_connect_gateway_id():
    module = FakeModule(state="present",
                        id_to_associate=None,
                        public=False,
                        name="aaaaaaaa",
                        vlan=1,
                        bgp_asn=123,
                        authentication_key="aaaa",
                        customer_address="169.254.0.1/30",
                        amazon_address="169.254.0.2/30",
                        address_type="ipv4",
                        cidr=["10.88.0.0/30"],
                        virtual_gateway_id=None,
                        direct_connect_gateway_id="yyyy")
    vi = aws_direct_connect_virtual_interface.assemble_params_for_creating_vi(module.params)
    print(vi)
    assert vi == {
        "virtualInterfaceName": "aaaaaaaa",
        "vlan": 1,
        "asn": 123,
        "authKey": "aaaa",
        "amazonAddress": "169.254.0.2/30",
        "customerAddress": "169.254.0.1/30",
        "addressFamily": "ipv4",
        "directConnectGatewayId": "yyyy"
    }


def test_create_public_vi(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    module = FakeModule(state="present",
                        id_to_associate='dxcon-aaaaaaaa',
                        virtual_interface_id=None,
                        public=True,
                        name="aaaaaaaa",
                        vlan=1,
                        bgp_asn=123,
                        authentication_key="aaaa",
                        customer_address="169.254.0.1/30",
                        amazon_address="169.254.0.2/30",
                        address_type="ipv4",
                        cidr=["10.88.0.0/30"],
                        virtual_gateway_id="xxxx",
                        direct_connect_gateway_id="yyyy")
    changed, latest_state = aws_direct_connect_virtual_interface.ensure_state(client, module)
    assert changed is True
    assert latest_state is not None


def test_create_private_vi(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    module = FakeModule(state="present",
                        id_to_associate='dxcon-aaaaaaaa',
                        virtual_interface_id=None,
                        public=False,
                        name="aaaaaaaa",
                        vlan=1,
                        bgp_asn=123,
                        authentication_key="aaaa",
                        customer_address="169.254.0.1/30",
                        amazon_address="169.254.0.2/30",
                        address_type="ipv4",
                        cidr=["10.88.0.0/30"],
                        virtual_gateway_id="xxxx",
                        direct_connect_gateway_id="yyyy")
    changed, latest_state = aws_direct_connect_virtual_interface.ensure_state(client, module)
    assert changed is True
    assert latest_state is not None


def test_delete_vi(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    module = FakeModule(state="absent",
                        id_to_associate='dxcon-aaaaaaaa',
                        virtual_interface_id='dxvif-aaaaaaaa',
                        public=False,
                        name="aaaaaaaa",
                        vlan=1,
                        bgp_asn=123,
                        authentication_key="aaaa",
                        customer_address="169.254.0.1/30",
                        amazon_address="169.254.0.2/30",
                        address_type="ipv4",
                        cidr=["10.88.0.0/30"],
                        virtual_gateway_id=None,
                        direct_connect_gateway_id="yyyy")
    changed, latest_state = aws_direct_connect_virtual_interface.ensure_state(client, module)
    assert changed is True
    assert latest_state == {}
