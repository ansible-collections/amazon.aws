from unittest.mock import MagicMock, Mock, patch, call

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_ami

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_ami"


def test_get_block_device_mapping_virtual_name():
    image = {
        "block_device_mappings": [
            {"device_name": "/dev/sdc", "virtual_name": "ephemeral0"}
        ]
    }
    block_device = ec2_ami.get_block_device_mapping(image)
    assert block_device == {"/dev/sdc": {"virtual_name": "ephemeral0"}}


def test_get_image_by_id_found():
    module = MagicMock()
    connection = MagicMock()

    connection.describe_images.return_value = {
        "Images": [{"ImageId": "ami-0c7a795306730b288"}]
    }

    image = ec2_ami.get_image_by_id(module, connection, "ami-0c7a795306730b288")
    assert image["ImageId"] == "ami-0c7a795306730b288"
    assert connection.describe_images.call_count == 1
    assert connection.describe_image_attribute.call_count == 2
    connection.describe_images.assert_has_calls(
        [
            call(
                aws_retry=True,
                ImageIds=["ami-0c7a795306730b288"],
            )
        ]
    )


def test_get_image_by_missing():
    module = MagicMock()
    connection = MagicMock()

    connection.describe_images.return_value = {"Images": []}

    image = ec2_ami.get_image_by_id(module, connection, "ami-0c7a795306730b288")
    assert image is None
    assert connection.describe_images.call_count == 1
    connection.describe_images.assert_has_calls(
        [
            call(
                aws_retry=True,
                ImageIds=["ami-0c7a795306730b288"],
            )
        ]
    )


@patch(
    module_name + ".get_image_by_id",
)
def test_create_image_minimal(m_get_image_by_id):
    module = MagicMock()
    connection = MagicMock()

    m_get_image_by_id.return_value = {"ImageId": "ami-0c7a795306730b288"}
    module.params = {
        "name": "my-image",
        "instance_id": "i-123456789",
        "image_id": "ami-0c7a795306730b288",
    }
    ec2_ami.create_image(module, connection)
    assert connection.create_image.call_count == 1
    connection.create_image.assert_has_calls(
        [
            call(
                aws_retry=True,
                Description=None,
                InstanceId="i-123456789",
                Name="my-image",
                NoReboot=None,
            )
        ]
    )
