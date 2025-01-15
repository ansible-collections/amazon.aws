# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_ami

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_ami"


@patch(module_name + ".register_image")
@patch(module_name + ".get_image_by_id")
def test_create_image_uefi_data(m_get_image_by_id, m_register_image):
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
    assert m_register_image.call_count == 1
    m_register_image.assert_has_calls(
        [
            call(
                connection,
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


@patch(module_name + ".describe_image_attribute")
@patch(module_name + ".describe_images")
def test_get_image_by_id_found(m_describe_images, m_describe_image_attribute):
    connection = MagicMock()

    m_describe_images.return_value = [{"ImageId": "ami-0c7a795306730b288"}]

    image = ec2_ami.get_image_by_id(connection, "ami-0c7a795306730b288")
    assert image["ImageId"] == "ami-0c7a795306730b288"
    assert m_describe_images.call_count == 1
    assert m_describe_image_attribute.call_count == 2
    m_describe_images.assert_has_calls(
        [
            call(
                connection,
                ImageIds=["ami-0c7a795306730b288"],
            )
        ]
    )


@patch(module_name + ".describe_images")
def test_get_image_by_too_many(m_describe_images):
    connection = MagicMock()

    m_describe_images.return_value = [
        {"ImageId": "ami-0c7a795306730b288"},
        {"ImageId": "ami-0c7a795306730b289"},
    ]

    with pytest.raises(ec2_ami.Ec2AmiFailure):
        ec2_ami.get_image_by_id(connection, "ami-0c7a795306730b288")
    m_describe_images.assert_called_once_with(connection, ImageIds=["ami-0c7a795306730b288"])


@patch(module_name + ".describe_images")
def test_get_image_missing(m_describe_images):
    connection = MagicMock()

    m_describe_images.return_value = []

    assert ec2_ami.get_image_by_id(connection, "ami-0c7a795306730b288") is None

    assert m_describe_images.call_count == 1
    m_describe_images.assert_has_calls(
        [
            call(
                connection,
                ImageIds=["ami-0c7a795306730b288"],
            )
        ]
    )


@patch(
    module_name + ".create_image",
)
@patch(
    module_name + ".get_image_by_id",
)
def test_create_image_minimal(m_get_image_by_id, m_create_image):
    module = MagicMock()
    connection = MagicMock()

    m_get_image_by_id.return_value = {"ImageId": "ami-0c7a795306730b288"}
    module.params = {
        "name": "my-image",
        "instance_id": "i-123456789",
        "image_id": "ami-0c7a795306730b288",
    }
    ec2_ami.CreateImage.do(module, connection, None)
    assert m_create_image.call_count == 1
    m_create_image.assert_has_calls(
        [
            call(
                connection,
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
    assert module.require_botocore_at_least.call_count == 0

    module = MagicMock()
    ec2_ami.validate_params(module, tpm_support=True, boot_mode="legacy-bios")
    assert module.require_botocore_at_least.call_count == 0
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


@patch(module_name + ".delete_snapshot")
def test_DeregisterImage_defer_purge_snapshots(m_delete_snapshot):
    image = {"BlockDeviceMappings": [{"Ebs": {"SnapshotId": "My_snapshot"}}, {}]}
    func = ec2_ami.DeregisterImage.defer_purge_snapshots(image)

    connection = MagicMock()
    assert list(func(connection)) == ["My_snapshot"]
    m_delete_snapshot.assert_called_with(connection, "My_snapshot")


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


def test_UpdateImage_set_launch_permission_check_mode_with_change():
    connection = MagicMock()
    image = {"ImageId": "ami-0c7a795306730b288", "LaunchPermissions": {}}
    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    changed = ec2_ami.UpdateImage.set_launch_permission(connection, image, launch_permissions, check_mode=True)
    assert changed is True
    assert connection.modify_image_attribute.call_count == 0


@patch(module_name + ".modify_image_attribute")
def test_UpdateImage_set_launch_permission_with_change(m_modify_image_attribute):
    connection = MagicMock()
    image = {"ImageId": "ami-0c7a795306730b288", "LaunchPermissions": {}}
    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    changed = ec2_ami.UpdateImage.set_launch_permission(connection, image, launch_permissions, check_mode=False)
    assert changed is True
    assert m_modify_image_attribute.call_count == 1
    m_modify_image_attribute.assert_called_with(
        connection,
        image_id="ami-0c7a795306730b288",
        Attribute="launchPermission",
        LaunchPermission={
            "Add": [{"Group": "bar"}, {"Group": "foo"}, {"UserId": "123456789012"}],
            "Remove": [],
        },
    )


@patch(module_name + ".modify_image_attribute")
def test_UpdateImage_set_description(m_modify_image_attribute):
    connection = MagicMock()
    module = MagicMock()
    module.check_mode = False
    image = {"ImageId": "ami-0c7a795306730b288", "Description": "My description"}
    changed = ec2_ami.UpdateImage.set_description(connection, module, image, "My description")
    assert changed is False

    changed = ec2_ami.UpdateImage.set_description(connection, module, image, "New description")
    assert changed is True
    assert m_modify_image_attribute.call_count == 1
    m_modify_image_attribute.assert_called_with(
        connection,
        image_id="ami-0c7a795306730b288",
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


@patch(module_name + ".describe_images")
def test_CreateImage_do_check_mode_with_change(m_describe_images):
    module = MagicMock()

    module.params = {"name": "my-image"}
    connection = MagicMock()
    m_describe_images.return_value = []

    ec2_ami.CreateImage.do_check_mode(module, connection, None)
    m_describe_images.assert_called_once_with(connection, Filters=[{"Name": "name", "Values": [module.params["name"]]}])
    module.exit_json.assert_called_with(changed=True, msg="Would have created a AMI if not in check mode.")


@patch(module_name + ".wait_for_resource_state")
def test_CreateImage_wait(m_wait_for_resource_state):
    connection = MagicMock()
    m_waiter = MagicMock()
    m_wait_for_resource_state.return_value = m_waiter
    module = MagicMock()
    module.params = {"wait": True, "wait_timeout": 0}
    assert ec2_ami.CreateImage.wait(connection, module, image_id=ANY) is None
    m_wait_for_resource_state.assert_not_called()

    module.params = {"wait": True, "wait_timeout": 600}
    image_id = "ami-0c7a795306730b288"
    ec2_ami.CreateImage.wait(connection, module, image_id=image_id)
    assert m_wait_for_resource_state.call_count == 1
    m_wait_for_resource_state.assert_called_with(
        connection, module, "image_available", delay=15, max_attempts=40, ImageIds=[image_id]
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


@patch(module_name + ".modify_image_attribute")
def test_CreateInage_set_launch_permissions(m_modify_image_attribute):
    connection = MagicMock()
    launch_permissions = {"user_ids": ["123456789012"], "group_names": ["foo", "bar"]}
    image_id = "ami-0c7a795306730b288"
    ec2_ami.CreateImage.set_launch_permissions(connection, launch_permissions, image_id)

    assert m_modify_image_attribute.call_count == 1
    m_modify_image_attribute.assert_called_with(
        connection,
        image_id="ami-0c7a795306730b288",
        Attribute="LaunchPermission",
        LaunchPermission={"Add": [{"Group": "foo"}, {"Group": "bar"}, {"UserId": "123456789012"}]},
    )
