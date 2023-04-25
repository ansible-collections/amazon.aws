# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_ami

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_ami"


@patch(module_name + ".get_image_by_id")
def test_create_image_uefi_data(m_get_image_by_id):
    module = MagicMock()
    connection = MagicMock()

    m_get_image_by_id.return_value = {
        "ImageId": "ami-0c7a795306730b288",
        "BootMode": "uefi",
        "TpmSupport": "v2.0",
    }

    module.params = {
        "name": "my-image",
        "boot_mode": "uefi",
        "tpm_support": "v2.0",
        "uefi_data": "QU1aTlVFRkk9xcN0AAAAAHj5a7fZ9+3aT2gcVRgA8Ek3NipiPST0pCiCIlTJtj20FzENCcQa",
    }

    ec2_ami.CreateImage.do(module, connection, None)
    assert connection.register_image.call_count == 1
    connection.register_image.assert_has_calls(
        [
            call(
                aws_retry=True,
                Name="my-image",
                BootMode="uefi",
                TpmSupport="v2.0",
                UefiData="QU1aTlVFRkk9xcN0AAAAAHj5a7fZ9+3aT2gcVRgA8Ek3NipiPST0pCiCIlTJtj20FzENCcQa",
            )
        ]
    )


def test_get_block_device_mapping_virtual_name():
    image = {"block_device_mappings": [{"device_name": "/dev/sdc", "virtual_name": "ephemeral0"}]}
    block_device = ec2_ami.get_block_device_mapping(image)
    assert block_device == {"/dev/sdc": {"virtual_name": "ephemeral0"}}


def test_get_image_by_id_found():
    connection = MagicMock()

    connection.describe_images.return_value = {"Images": [{"ImageId": "ami-0c7a795306730b288"}]}

    image = ec2_ami.get_image_by_id(connection, "ami-0c7a795306730b288")
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


def test_get_image_by_too_many():
    connection = MagicMock()

    connection.describe_images.return_value = {
        "Images": [
            {"ImageId": "ami-0c7a795306730b288"},
            {"ImageId": "ami-0c7a795306730b288"},
        ]
    }

    with pytest.raises(ec2_ami.Ec2AmiFailure):
        ec2_ami.get_image_by_id(connection, "ami-0c7a795306730b288")


def test_get_image_missing():
    connection = MagicMock()

    connection.describe_images.return_value = {"Images": []}

    image = ec2_ami.get_image_by_id(connection, "ami-0c7a795306730b288")
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
    ec2_ami.CreateImage.do(module, connection, None)
    assert connection.create_image.call_count == 1
    connection.create_image.assert_has_calls(
        [
            call(
                aws_retry=True,
                InstanceId="i-123456789",
                Name="my-image",
            )
        ]
    )


def test_validate_params():
    module = MagicMock()

    ec2_ami.validate_params(module)
    module.fail_json.assert_any_call("one of the following is required: name, image_id")
    assert module.require_botocore_at_least.call_count == 0

    module = MagicMock()
    ec2_ami.validate_params(module, tpm_support=True)
    assert module.require_botocore_at_least.call_count == 1

    module = MagicMock()
    ec2_ami.validate_params(module, tpm_support=True, boot_mode="legacy-bios")
    assert module.require_botocore_at_least.call_count == 1
    module.fail_json.assert_any_call("To specify 'tpm_support', 'boot_mode' must be 'uefi'.")

    module = MagicMock()
    ec2_ami.validate_params(module, state="present", name="bobby")
    assert module.require_botocore_at_least.call_count == 0
    module.fail_json.assert_any_call(
        "The parameters instance_id or device_mapping (register from EBS snapshot) are required for a new image."
    )


def test_rename_item_if_exists():
    dict_object = {
        "Paris": True,
        "London": {"Heathrow Airport": False},
    }
    ec2_ami.rename_item_if_exists(dict_object, "Paris", "NewYork")
    assert dict_object == {"London": {"Heathrow Airport": False}, "NewYork": True}

    dict_object = {
        "Cities": {},
        "London": "bar",
    }

    ec2_ami.rename_item_if_exists(dict_object, "London", "Abidjan", "Cities")
    ec2_ami.rename_item_if_exists(dict_object, "Doesnt-exist", "Nowhere", "Cities")
    assert dict_object == {"Cities": {"Abidjan": "bar"}}


def test_DeregisterImage_defer_purge_snapshots():
    image = {"BlockDeviceMappings": [{"Ebs": {"SnapshotId": "My_snapshot"}}, {}]}
    func = ec2_ami.DeregisterImage.defer_purge_snapshots(image)

    connection = MagicMock()
    assert list(func(connection)) == ["My_snapshot"]
    connection.delete_snapshot.assert_called_with(aws_retry=True, SnapshotId="My_snapshot")


@patch(module_name + ".get_image_by_id")
@patch(module_name + ".time.sleep")
def test_DeregisterImage_timeout_success(m_sleep, m_get_image_by_id):
    connection = MagicMock()
    m_get_image_by_id.side_effect = [{"ImageId": "ami-0c7a795306730b288"}, None]

    ec2_ami.DeregisterImage.timeout(connection, "ami-0c7a795306730b288", 10)
    assert m_sleep.call_count == 1


@patch(module_name + ".get_image_by_id")
@patch(module_name + ".time.time")
@patch(module_name + ".time.sleep")
def test_DeregisterImage_timeout_failure(m_sleep, m_time, m_get_image_by_id):
    connection = MagicMock()
    m_time.side_effect = list(range(1, 30))
    m_get_image_by_id.return_value = {"ImageId": "ami-0c7a795306730b288"}

    with pytest.raises(ec2_ami.Ec2AmiFailure):
        ec2_ami.DeregisterImage.timeout(connection, "ami-0c7a795306730b288", 10)
    assert m_sleep.call_count == 9


def test_UpdateImage_set_launch_permission_check_mode_no_change():
    connection = MagicMock()
    image = {"ImageId": "ami-0c7a795306730b288", "LaunchPermissions": {}}

    changed = ec2_ami.UpdateImage.set_launch_permission(connection, image, launch_permissions={}, check_mode=True)
    assert changed is False
    assert connection.modify_image_attribute.call_count == 0

    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    image = {
        "ImageId": "ami-0c7a795306730b288",
        "LaunchPermissions": [
            {"UserId": "123456789012"},
            {"GroupName": "foo"},
            {"GroupName": "bar"},
        ],
    }


def test_UpdateImage_set_launch_permission_check_mode_with_change():
    connection = MagicMock()
    image = {"ImageId": "ami-0c7a795306730b288", "LaunchPermissions": {}}
    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    changed = ec2_ami.UpdateImage.set_launch_permission(connection, image, launch_permissions, check_mode=True)
    assert changed is True
    assert connection.modify_image_attribute.call_count == 0


def test_UpdateImage_set_launch_permission_with_change():
    connection = MagicMock()
    image = {"ImageId": "ami-0c7a795306730b288", "LaunchPermissions": {}}
    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    changed = ec2_ami.UpdateImage.set_launch_permission(connection, image, launch_permissions, check_mode=False)
    assert changed is True
    assert connection.modify_image_attribute.call_count == 1
    connection.modify_image_attribute.assert_called_with(
        aws_retry=True,
        ImageId="ami-0c7a795306730b288",
        Attribute="launchPermission",
        LaunchPermission={
            "Add": [{"Group": "bar"}, {"Group": "foo"}, {"UserId": "123456789012"}],
            "Remove": [],
        },
    )


def test_UpdateImage_set_description():
    connection = MagicMock()
    module = MagicMock()
    module.check_mode = False
    image = {"ImageId": "ami-0c7a795306730b288", "Description": "My description"}
    changed = ec2_ami.UpdateImage.set_description(connection, module, image, "My description")
    assert changed is False

    changed = ec2_ami.UpdateImage.set_description(connection, module, image, "New description")
    assert changed is True
    assert connection.modify_image_attribute.call_count == 1
    connection.modify_image_attribute.assert_called_with(
        aws_retry=True,
        ImageId="ami-0c7a795306730b288",
        Attribute="Description",
        Description={"Value": "New description"},
    )


def test_UpdateImage_set_description_check_mode():
    connection = MagicMock()
    module = MagicMock()
    module.check_mode = True
    image = {"ImageId": "ami-0c7a795306730b288", "Description": "My description"}
    changed = ec2_ami.UpdateImage.set_description(connection, module, image, "My description")
    assert changed is False

    changed = ec2_ami.UpdateImage.set_description(connection, module, image, "New description")
    assert changed is True
    assert connection.modify_image_attribute.call_count == 0


def test_CreateImage_build_block_device_mapping():
    device_mapping = [
        {
            "device_name": "/dev/xvda",
            "volume_size": 8,
            "snapshot_id": "snap-xxxxxxxx",
            "delete_on_termination": True,
            "volume_type": "gp2",
            "no_device": False,
        },
        {
            "device_name": "/dev/xvdb",
            "no_device": True,
        },
    ]
    result = ec2_ami.CreateImage.build_block_device_mapping(device_mapping)
    assert result == [
        {
            "Ebs": {
                "DeleteOnTermination": True,
                "SnapshotId": "snap-xxxxxxxx",
                "VolumeSize": 8,
                "VolumeType": "gp2",
            },
            "DeviceName": "/dev/xvda",
        },
        {"DeviceName": "/dev/xvdb", "Ebs": {}, "NoDevice": ""},
    ]


def test_CreateImage_do_check_mode_no_change():
    module = MagicMock()

    module.params = {"name": "my-image"}
    connection = MagicMock()
    connection.describe_images.return_value = {
        "Images": [
            {
                "InstanceId": "i-123456789",
                "Name": "my-image",
            }
        ]
    }

    ec2_ami.CreateImage.do_check_mode(module, connection, None)
    module.exit_json.assert_called_with(
        changed=False,
        msg="Error registering image: AMI name is already in use by another AMI",
    )


def test_CreateImage_do_check_mode_with_change():
    module = MagicMock()

    module.params = {"name": "my-image"}
    connection = MagicMock()
    connection.describe_images.return_value = {"Images": []}

    ec2_ami.CreateImage.do_check_mode(module, connection, None)
    module.exit_json.assert_called_with(changed=True, msg="Would have created a AMI if not in check mode.")


@patch(module_name + ".get_waiter")
def test_CreateImage_wait(m_get_waiter):
    connection = MagicMock()
    m_waiter = MagicMock()
    m_get_waiter.return_value = m_waiter

    assert ec2_ami.CreateImage.wait(connection, wait_timeout=0, image_id=None) is None

    ec2_ami.CreateImage.wait(connection, wait_timeout=600, image_id="ami-0c7a795306730b288")
    assert m_waiter.wait.call_count == 1
    m_waiter.wait.assert_called_with(
        ImageIds=["ami-0c7a795306730b288"],
        WaiterConfig={"Delay": 15, "MaxAttempts": 40},
    )


@patch(module_name + ".add_ec2_tags")
@patch(module_name + ".get_image_by_id")
def test_CreateImage_set_tags(m_get_image_by_id, m_add_ec2_tags):
    connection = MagicMock()
    module = MagicMock()

    m_get_image_by_id.return_value = {
        "ImageId": "ami-0c7a795306730b288",
        "BlockDeviceMappings": [
            {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": "50"}},
            {
                "DeviceName": "/dev/sdm",
                "Ebs": {"VolumeSize": "100", "SnapshotId": "snap-066877671789bd71b"},
            },
            {"DeviceName": "/dev/sda2"},
        ],
    }
    tags = {}
    ec2_ami.CreateImage.set_tags(connection, module, tags, image_id="ami-0c7a795306730b288")
    assert m_add_ec2_tags.call_count == 0

    tags = {"metro": "LaSalle"}
    ec2_ami.CreateImage.set_tags(connection, module, tags, image_id="ami-0c7a795306730b288")
    assert m_add_ec2_tags.call_count == 3
    m_add_ec2_tags.assert_called_with(connection, module, "snap-066877671789bd71b", tags)


def test_CreateInage_set_launch_permissions():
    connection = MagicMock()
    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    image_id = "ami-0c7a795306730b288"
    ec2_ami.CreateImage.set_launch_permissions(connection, launch_permissions, image_id)

    assert connection.modify_image_attribute.call_count == 1
    connection.modify_image_attribute.assert_called_with(
        Attribute="LaunchPermission",
        ImageId="ami-0c7a795306730b288",
        LaunchPermission={"Add": [{"Group": "foo"}, {"Group": "bar"}, {"UserId": "123456789012"}]},
        aws_retry=True,
    )
