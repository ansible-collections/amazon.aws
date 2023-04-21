# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from unittest.mock import MagicMock, patch, ANY, call
import botocore.exceptions
import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_ami_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_ami_info"


@pytest.fixture
def ec2_client():
    return MagicMock()


@pytest.mark.parametrize(
    "executable_users,filters,image_ids,owners,expected",
    [
        ([], {}, [], [], {}),
        ([], {}, ["ami-1234567890"], [], {"ImageIds": ["ami-1234567890"]}),
        ([], {}, [], ["1234567890"], {"Filters": [{"Name": "owner-id", "Values": ["1234567890"]}]}),
        (
            [],
            {"owner-alias": "test_ami_owner"},
            [],
            ["1234567890"],
            {
                "Filters": [
                    {"Name": "owner-alias", "Values": ["test_ami_owner"]},
                    {"Name": "owner-id", "Values": ["1234567890"]},
                ]
            },
        ),
        ([], {"is-public": True}, [], [], {"Filters": [{"Name": "is-public", "Values": ["true"]}]}),
        (["self"], {}, [], [], {"ExecutableUsers": ["self"]}),
        ([], {}, [], ["self"], {"Owners": ["self"]}),
    ],
)
def test_build_request_args(executable_users, filters, image_ids, owners, expected):
    assert ec2_ami_info.build_request_args(executable_users, filters, image_ids, owners) == expected


def test_get_images(ec2_client):
    ec2_client.describe_images.return_value = {
        "Images": [
            {
                "Architecture": "x86_64",
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                            "DeleteOnTermination": "True",
                            "Encrypted": "False",
                            "SnapshotId": "snap-0f00cba784af62428",
                            "VolumeSize": 10,
                            "VolumeType": "gp2",
                        },
                    }
                ],
                "ImageId": "ami-1234567890",
                "ImageLocation": "1234567890/test-ami-uefi-boot",
                "ImageType": "machine",
                "Name": "test-ami-uefi-boot",
                "OwnerId": "1234567890",
                "PlatformDetails": "Linux/UNIX",
            }
        ],
    }

    request_args = {"ImageIds": ["ami-1234567890"]}

    get_images_result = ec2_ami_info.get_images(ec2_client, request_args)

    ec2_client.describe_images.call_count == 2
    ec2_client.describe_images.assert_called_with(aws_retry=True, **request_args)
    assert get_images_result == ec2_client.describe_images.return_value


def test_get_image_attribute():
    ec2_client = MagicMock()

    ec2_client.describe_image_attribute.return_value = {
        "ImageId": "ami-1234567890",
        "LaunchPermissions": [{"UserId": "1234567890"}, {"UserId": "0987654321"}],
    }

    image = {
        "architecture": "x86_64",
        "blockDeviceMappings": [
            {
                "device_name": "/dev/sda1",
                "ebs": {
                    "delete_on_termination": "True",
                    "encrypted": "False",
                    "snapshot_id": "snap-0f00cba784af62428",
                    "volume_size": 10,
                    "volume_Type": "gp2",
                },
            }
        ],
        "image_id": "ami-1234567890",
        "image_location": "1234567890/test-ami-uefi-boot",
        "image_type": "machine",
        "name": "test-ami-uefi-boot",
        "owner_id": "1234567890",
        "platform_details": "Linux/UNIX",
    }

    get_image_attribute_result = ec2_ami_info.get_image_attribute(ec2_client, image)

    ec2_client.describe_image_attribute.call_count == 1
    ec2_client.describe_image_attribute.assert_called_with(
        aws_retry=True, Attribute="launchPermission", ImageId=image["image_id"]
    )
    assert len(get_image_attribute_result["LaunchPermissions"]) == 2


@patch(module_name + ".get_image_attribute")
@patch(module_name + ".get_images")
def test_list_ec2_images(m_get_images, m_get_image_attribute):
    module = MagicMock()

    m_get_images.return_value = {
        "Images": [
            {
                "Architecture": "x86_64",
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                            "DeleteOnTermination": "True",
                            "Encrypted": "False",
                            "SnapshotId": "snap-0f00cba784af62428",
                            "VolumeSize": 10,
                            "VolumeType": "gp2",
                        },
                    }
                ],
                "ImageId": "ami-1234567890",
                "ImageLocation": "1234567890/test-ami-uefi-boot",
                "ImageType": "machine",
                "Name": "test-ami-uefi-boot",
                "OwnerId": "1234567890",
                "OwnerAlias": "test_ami_owner",
                "PlatformDetails": "Linux/UNIX",
            },
            {
                "Architecture": "x86_64",
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                            "DeleteOnTermination": "True",
                            "Encrypted": "False",
                            "SnapshotId": "snap-0f00cba784af62428",
                            "VolumeSize": 10,
                            "VolumeType": "gp2",
                        },
                    }
                ],
                "ImageId": "ami-1523498760",
                "ImageLocation": "1523498760/test-ami-uefi-boot",
                "ImageType": "machine",
                "Name": "test-ami-uefi-boot",
                "OwnerId": "1234567890",
                "OwnerAlias": "test_ami_owner",
                "PlatformDetails": "Linux/UNIX",
            },
        ],
    }

    m_get_image_attribute.return_value = {
        "ImageId": "ami-1234567890",
        "LaunchPermissions": [{"UserId": "1234567890"}, {"UserId": "0987654321"}],
    }

    images = m_get_images.return_value["Images"]
    images = [camel_dict_to_snake_dict(image) for image in images]

    request_args = {
        "Filters": [
            {"Name": "owner-alias", "Values": ["test_ami_owner"]},
            {"Name": "owner-id", "Values": ["1234567890"]},
        ]
    }

    # needed for `assert m_get_image_attribute.call_count == 2`
    module.params = {"describe_image_attributes": True}

    list_ec2_images_result = ec2_ami_info.list_ec2_images(ec2_client, module, request_args)

    assert m_get_images.call_count == 1
    m_get_images.assert_called_with(ec2_client, request_args)

    assert m_get_image_attribute.call_count == 2
    assert m_get_image_attribute.has_calls([call(ec2_client, images[0])], [call(ec2_client, images[1])])

    assert len(list_ec2_images_result) == 2
    assert list_ec2_images_result[0]["image_id"] == "ami-1234567890"
    assert list_ec2_images_result[1]["image_id"] == "ami-1523498760"


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_ami_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)
    m_module.exit_json.assert_called_with(images=[])


def a_boto_exception():
    return botocore.exceptions.UnknownServiceError(service_name="Whoops", known_service_names="Oula")


def test_api_failure_get_images(ec2_client):
    request_args = {}
    ec2_client.describe_images.side_effect = a_boto_exception()

    with pytest.raises(ec2_ami_info.AmiInfoFailure):
        ec2_ami_info.get_images(ec2_client, request_args)


def test_api_failure_get_image_attribute(ec2_client):
    image = {"image_id": "ami-1234567890"}
    ec2_client.describe_image_attribute.side_effect = a_boto_exception()

    with pytest.raises(ec2_ami_info.AmiInfoFailure):
        ec2_ami_info.get_image_attribute(ec2_client, image)
