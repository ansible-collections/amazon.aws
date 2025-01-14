# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_vpc_net

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_vpc_net"


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.check_mode = False
    module.params = {}
    module.fail_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(1)

    return module


@patch(module_name + ".ansible_dict_to_boto3_filter_list")
@patch(module_name + ".describe_vpcs")
def test_get_vpc_id_no_id(m_describe_vpcs, m_ansible_dict_to_boto3_filter_list, ansible_module):
    connection = MagicMock()
    cidr_block = MagicMock()
    vpc_id = MagicMock()

    m_ansible_dict_to_boto3_filter_list.return_value = MagicMock()
    ansible_module.params.update({"cidr_block": cidr_block})
    m_describe_vpcs.return_value = [{"VpcId": vpc_id}]

    assert ec2_vpc_net.get_vpc_id(connection, ansible_module) == vpc_id
    m_ansible_dict_to_boto3_filter_list.assert_called_once_with(
        {"tag:Name": ansible_module.params.get("name"), "cidr-block": cidr_block}
    )
    m_describe_vpcs.assert_called_once_with(connection, Filters=m_ansible_dict_to_boto3_filter_list.return_value)


@pytest.mark.parametrize("multi_ok", [True, False])
@patch(module_name + ".ansible_dict_to_boto3_filter_list")
@patch(module_name + ".describe_vpcs")
def test_get_vpc_id_multiple(m_describe_vpcs, m_ansible_dict_to_boto3_filter_list, ansible_module, multi_ok):
    connection = MagicMock()
    cidr_block = MagicMock()
    vpc_id = MagicMock()
    another_vpc_id = MagicMock()

    m_ansible_dict_to_boto3_filter_list.return_value = MagicMock()
    ansible_module.params.update({"cidr_block": cidr_block, "multi_ok": multi_ok})
    m_describe_vpcs.return_value = [{"VpcId": vpc_id}, {"VpcId": another_vpc_id}]

    if multi_ok:
        assert not ec2_vpc_net.get_vpc_id(connection, ansible_module)
    else:
        with pytest.raises(SystemExit):
            ec2_vpc_net.get_vpc_id(connection, ansible_module)

    m_ansible_dict_to_boto3_filter_list.assert_called_once_with(
        {"tag:Name": ansible_module.params.get("name"), "cidr-block": cidr_block}
    )
    m_describe_vpcs.assert_called_once_with(connection, Filters=m_ansible_dict_to_boto3_filter_list.return_value)


@patch(module_name + ".ansible_dict_to_boto3_filter_list")
@patch(module_name + ".describe_vpcs")
def test_get_vpc_id_cidr_block_list(m_describe_vpcs, m_ansible_dict_to_boto3_filter_list, ansible_module):
    connection = MagicMock()
    cidr_block = [MagicMock(), MagicMock()]
    vpc_id = MagicMock()
    vpc_filters = [MagicMock(), MagicMock()]

    m_ansible_dict_to_boto3_filter_list.side_effect = vpc_filters
    ansible_module.params.update({"cidr_block": cidr_block})
    m_describe_vpcs.side_effect = [[], [{"VpcId": vpc_id}]]

    assert ec2_vpc_net.get_vpc_id(connection, ansible_module) == vpc_id
    m_ansible_dict_to_boto3_filter_list.assert_has_calls(
        [
            call({"tag:Name": ansible_module.params.get("name"), "cidr-block": cidr_block}),
            call({"tag:Name": ansible_module.params.get("name"), "cidr-block": [cidr_block[0]]}),
        ]
    )
    m_describe_vpcs.assert_has_calls(
        [
            call(connection, Filters=vpc_filters[0]),
            call(connection, Filters=vpc_filters[1]),
        ]
    )


@pytest.mark.parametrize("cidr_block", [None, []])
@patch(module_name + ".disassociate_vpc_cidr_block")
@patch(module_name + ".associate_vpc_cidr_block")
def test_update_cidrs_no_cidr_block(
    m_associate_vpc_cidr_block, m_disassociate_vpc_cidr_block, ansible_module, cidr_block
):
    connection = MagicMock()
    vpc_obj = {}
    cidr_block = []
    changed, desired_cidrs = ec2_vpc_net.update_cidrs(connection, ansible_module, vpc_obj, cidr_block, ANY)
    assert not changed
    assert desired_cidrs is None

    m_associate_vpc_cidr_block.assert_not_called()
    m_disassociate_vpc_cidr_block.assert_not_called()


@pytest.mark.parametrize("check_mode", [True, False])
@pytest.mark.parametrize(
    "associated_cidrs, cidr_block, purge_cidrs, add, remove, expected",
    [
        (
            [
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.1.0.0/24",
                    "CidrBlockState": {"State": "associated"},
                },
            ],
            ["10.1.0.0/24"],
            True,
            [],
            [],
            (False, None),
        ),
        (
            [
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.1.0.0/24",
                    "CidrBlockState": {"State": "associated"},
                },
            ],
            ["10.1.0.0/24"],
            False,
            [],
            [],
            (False, None),
        ),
        (
            [
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.1.0.0/24",
                    "CidrBlockState": {"State": "associated"},
                },
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.2.0.0/24",
                    "CidrBlockState": {"State": "failed"},
                },
            ],
            ["10.1.0.0/24"],
            True,
            [],
            [],
            (True, ["10.1.0.0/24"]),
        ),
        (
            [
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.1.0.0/24",
                    "CidrBlockState": {"State": "associated"},
                },
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.2.0.0/24",
                    "CidrBlockState": {"State": "failed"},
                },
            ],
            ["10.1.0.0/24"],
            False,
            [],
            [],
            (False, None),
        ),
        (
            [
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.1.0.0/24",
                    "CidrBlockState": {"State": "associated"},
                },
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.2.0.0/24",
                    "CidrBlockState": {"State": "disassociating"},
                },
            ],
            ["10.2.0.0/24"],
            False,
            ["10.2.0.0/24"],
            [],
            (True, ["10.1.0.0/24", "10.2.0.0/24"]),
        ),
        (
            [
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.1.0.0/24",
                    "CidrBlockState": {"State": "associated"},
                },
                {
                    "AssociationId": "vpc-cidr-assoc-001",
                    "CidrBlock": "10.2.0.0/24",
                    "CidrBlockState": {"State": "disassociating"},
                },
            ],
            ["10.2.0.0/24"],
            True,
            ["10.2.0.0/24"],
            ["vpc-cidr-assoc-001"],
            (True, ["10.2.0.0/24"]),
        ),
    ],
)
@patch(module_name + ".disassociate_vpc_cidr_block")
@patch(module_name + ".associate_vpc_cidr_block")
def test_update_cidrs_no_purge(
    m_associate_vpc_cidr_block,
    m_disassociate_vpc_cidr_block,
    ansible_module,
    check_mode,
    associated_cidrs,
    cidr_block,
    purge_cidrs,
    add,
    remove,
    expected,
):
    connection = MagicMock()
    vpc_obj = {"VpcId": MagicMock(), "CidrBlockAssociationSet": associated_cidrs}
    ansible_module.check_mode = check_mode
    changed, desired_cidrs = ec2_vpc_net.update_cidrs(connection, ansible_module, vpc_obj, cidr_block, purge_cidrs)
    assert expected[0] == changed

    def sorted_list(x):
        return x if not x else sorted(x)

    assert sorted_list(expected[1]) == sorted_list(desired_cidrs)

    if not expected[0] or check_mode:
        m_associate_vpc_cidr_block.assert_not_called()
        m_disassociate_vpc_cidr_block.assert_not_called()
    else:
        if add:
            m_associate_vpc_cidr_block.assert_has_calls(
                [call(connection, vpc_id=vpc_obj["VpcId"], CidrBlock=cidr) for cidr in add], any_order=True
            )
        else:
            m_associate_vpc_cidr_block.assert_not_called()

        if remove:
            m_disassociate_vpc_cidr_block.assert_has_calls(
                [call(connection, association_id) for association_id in remove], any_order=False
            )
