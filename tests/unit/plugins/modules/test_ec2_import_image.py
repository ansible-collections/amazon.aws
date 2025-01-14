# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_import_image
from ansible_collections.amazon.aws.plugins.modules import ec2_import_image_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_import_image"
module_name_info = "ansible_collections.amazon.aws.plugins.modules.ec2_import_image_info"
utils = "ansible_collections.amazon.aws.plugins.module_utils.ec2"

p_expected_result = {
    "import_task_id": "import-ami-0c207d759080a3dff",
    "progress": "19",
    "snapshot_details": [
        {
            "disk_image_size": 26843545600.0,
            "format": "RAW",
            "status": "active",
            "user_bucket": {"s3_bucket": "clone-vm-s3-bucket", "s3_key": "clone-vm-s3-bucket/ubuntu-vm-clone.raw"},
        }
    ],
    "status": "active",
    "status_message": "converting",
    "tags": {"Name": "clone-vm-import-image"},
    "task_name": "clone-vm-import-image",
}

p_describe_import_image_tasks = [
    {
        "import_task_id": "import-ami-0c207d759080a3dff",
        "progress": "19",
        "snapshot_details": [
            {
                "disk_image_size": 26843545600.0,
                "format": "RAW",
                "status": "active",
                "user_bucket": {"s3_bucket": "clone-vm-s3-bucket", "s3_key": "clone-vm-s3-bucket/ubuntu-vm-clone.raw"},
            }
        ],
        "status": "active",
        "status_message": "converting",
        "tags": {"Name": "clone-vm-import-image"},
    }
]


@pytest.fixture(name="module")
def fixture_module():
    # Create a MagicMock for the module object
    module_mock = MagicMock()
    module_mock.params = {
        "task_name": "clone-vm-import-image",
        "disk_containers": [
            {
                "format": "raw",
                "user_bucket": {"s3_bucket": "clone-vm-s3-bucket", "s3_key": "clone-vm-s3-bucket/ubuntu-vm-clone.raw"},
            }
        ],
    }
    module_mock.check_mode = False

    return module_mock


@pytest.mark.parametrize(
    "import_image_info, expected_result",
    [
        (
            [[], p_describe_import_image_tasks],
            {"changed": True, "import_image": p_expected_result},
        ),
        (
            [p_describe_import_image_tasks, p_describe_import_image_tasks],
            {
                "changed": False,
                "msg": "An import task with the specified name already exists",
                "import_image": p_expected_result,
            },
        ),
    ],
)
@patch(module_name + ".import_image")
@patch(module_name + ".describe_import_image_tasks_as_snake_dict")
def test_present_no_check_mode(
    m_describe_import_image_tasks_as_snake_dict, m_import_image, module, import_image_info, expected_result
):
    m_describe_import_image_tasks_as_snake_dict.side_effect = import_image_info
    module.exit_json.side_effect = SystemExit(1)
    connection = MagicMock()

    with pytest.raises(SystemExit):
        ec2_import_image.present(connection, module)

    if import_image_info:
        m_import_image.call_count = 1
        m_describe_import_image_tasks_as_snake_dict.call_count = 2
    else:
        m_import_image.assert_not_called()
        m_describe_import_image_tasks_as_snake_dict.call_count = 1
    module.exit_json.assert_called_with(**expected_result)


@pytest.mark.parametrize(
    "import_image_info, expected_result",
    [
        (
            [],
            {"changed": True, "msg": "Would have created the import task if not in check mode"},
        ),
        (
            p_describe_import_image_tasks,
            {
                "changed": False,
                "msg": "An import task with the specified name already exists",
                "import_image": p_expected_result,
            },
        ),
    ],
)
@patch(module_name + ".import_image")
@patch(module_name + ".describe_import_image_tasks_as_snake_dict")
def test_present_check_mode(
    m_describe_import_image_tasks_as_snake_dict, m_import_image, module, import_image_info, expected_result
):
    m_describe_import_image_tasks_as_snake_dict.return_value = import_image_info
    module.check_mode = True
    module.exit_json.side_effect = SystemExit(1)
    connection = MagicMock()

    with pytest.raises(SystemExit):
        ec2_import_image.present(connection, module)

    m_import_image.assert_not_called()
    module.exit_json.assert_called_with(**expected_result)


@pytest.mark.parametrize(
    "import_image_info, expected_result",
    [
        (
            [],
            {
                "changed": False,
                "msg": "The specified import task does not exist or it cannot be cancelled",
                "import_image": {},
            },
        ),
        (
            p_describe_import_image_tasks,
            {"changed": True, "import_image": p_expected_result},
        ),
    ],
)
@patch(module_name + ".cancel_import_task")
@patch(module_name + ".describe_import_image_tasks_as_snake_dict")
def test_absent_no_check_mode(
    m_describe_import_image_tasks_as_snake_dict, m_cancel_import_task, module, import_image_info, expected_result
):
    module.exit_json.side_effect = SystemExit(1)
    connection = MagicMock()
    m_describe_import_image_tasks_as_snake_dict.return_value = import_image_info
    m_cancel_import_task.return_value = True

    with pytest.raises(SystemExit):
        ec2_import_image.absent(connection, module)

    if import_image_info:
        m_cancel_import_task.assert_called_with(
            connection,
            import_task_id=import_image_info[0]["import_task_id"],
            cancel_reason=module.params.get("cancel_reason"),
        )
    module.exit_json.assert_called_with(**expected_result)


@pytest.mark.parametrize(
    "import_image_info, expected_result",
    [
        (
            [],
            {
                "changed": False,
                "msg": "The specified import task does not exist or it cannot be cancelled",
                "import_image": {},
            },
        ),
        (
            p_describe_import_image_tasks,
            {"changed": True, "msg": "Would have cancelled the import task if not in check mode"},
        ),
    ],
)
@patch(module_name + ".cancel_import_task")
@patch(module_name + ".describe_import_image_tasks_as_snake_dict")
def test_absent_check_mode(
    m_describe_import_image_tasks_as_snake_dict, m_cancel_import_task, module, import_image_info, expected_result
):
    module.exit_json.side_effect = SystemExit(1)
    module.check_mode = True
    m_describe_import_image_tasks_as_snake_dict.return_value = import_image_info
    connection = MagicMock()

    with pytest.raises(SystemExit):
        ec2_import_image.absent(connection, module)

    m_cancel_import_task.assert_not_called()
    module.exit_json.assert_called_with(**expected_result)


@patch(module_name_info + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_import_image_info.main()

    m_module.client.assert_called_with("ec2")
