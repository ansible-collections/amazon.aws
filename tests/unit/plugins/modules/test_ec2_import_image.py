# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_import_image
from ansible_collections.amazon.aws.plugins.modules import ec2_import_image_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_import_image"
module_name_info = "ansible_collections.amazon.aws.plugins.modules.ec2_import_image_info"
utils = "ansible_collections.amazon.aws.plugins.module_utils.ec2"

expected_result = {
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

describe_import_image_tasks = [
    {
        "ImportTaskId": "import-ami-0c207d759080a3dff",
        "Progress": "19",
        "SnapshotDetails": [
            {
                "DiskImageSize": 26843545600.0,
                "Format": "RAW",
                "Status": "active",
                "UserBucket": {"S3Bucket": "clone-vm-s3-bucket", "S3Key": "clone-vm-s3-bucket/ubuntu-vm-clone.raw"},
            }
        ],
        "Status": "active",
        "StatusMessage": "converting",
        "Tags": [{"Key": "Name", "Value": "clone-vm-import-image"}],
    }
]


@pytest.fixture
def paginate():
    # Create a MagicMock for the paginate object
    paginate_mock = MagicMock()

    return paginate_mock


@pytest.fixture
def conn_paginator(paginate):
    conn_paginator_mock = MagicMock()
    conn_paginator_mock.paginate.return_value = paginate
    return conn_paginator_mock


@pytest.fixture
def client(conn_paginator):
    client_mock = MagicMock()

    # Configure the client.get_paginator to return the conn_paginator
    client_mock.get_paginator.return_value = conn_paginator

    return client_mock


@pytest.fixture
def module():
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
    "side_effects, expected_result",
    [
        (
            [{"ImportImageTasks": []}, {"ImportImageTasks": describe_import_image_tasks}],
            {"changed": True, "import_image": expected_result},
        ),
        (
            [{"ImportImageTasks": describe_import_image_tasks}, {"ImportImageTasks": describe_import_image_tasks}],
            {
                "changed": False,
                "msg": "An import task with the specified name already exists",
                "import_image": expected_result,
            },
        ),
    ],
)
def test_present_no_check_mode(client, module, paginate, side_effects, expected_result):
    paginate.build_full_result.side_effect = side_effects
    module.exit_json.side_effect = SystemExit(1)

    with patch(utils + ".helper_describe_import_image_tasks", return_value=paginate):
        with pytest.raises(SystemExit):
            ec2_import_image.present(client, module)

    module.exit_json.assert_called_with(**expected_result)


@pytest.mark.parametrize(
    "side_effects, expected_result",
    [
        (
            [{"ImportImageTasks": []}, {"ImportImageTasks": describe_import_image_tasks}],
            {"changed": True, "msg": "Would have created the import task if not in check mode"},
        ),
        (
            [{"ImportImageTasks": describe_import_image_tasks}, {"ImportImageTasks": describe_import_image_tasks}],
            {
                "changed": False,
                "msg": "An import task with the specified name already exists",
                "import_image": expected_result,
            },
        ),
    ],
)
def test_present_check_mode(client, module, paginate, side_effects, expected_result):
    paginate.build_full_result.side_effect = side_effects
    module.check_mode = True
    module.exit_json.side_effect = SystemExit(1)

    with patch(utils + ".helper_describe_import_image_tasks", return_value=paginate):
        with pytest.raises(SystemExit):
            ec2_import_image.present(client, module)

    module.exit_json.assert_called_with(**expected_result)


@pytest.mark.parametrize(
    "side_effect, expected_result",
    [
        (
            [
                {"ImportImageTasks": []},
            ],
            {
                "changed": False,
                "msg": "The specified import task does not exist or it cannot be cancelled",
                "import_image": {},
            },
        ),
        (
            [
                {"ImportImageTasks": describe_import_image_tasks},
            ],
            {"changed": True, "import_image": expected_result},
        ),
    ],
)
def test_absent_no_check_mode(client, module, paginate, side_effect, expected_result):
    paginate.build_full_result.side_effect = side_effect
    module.exit_json.side_effect = SystemExit(1)

    with patch(utils + ".helper_describe_import_image_tasks", return_value=paginate):
        with pytest.raises(SystemExit):
            ec2_import_image.absent(client, module)

    module.exit_json.assert_called_with(**expected_result)


@pytest.mark.parametrize(
    "side_effect, expected_result",
    [
        (
            [
                {"ImportImageTasks": []},
            ],
            {
                "changed": False,
                "msg": "The specified import task does not exist or it cannot be cancelled",
                "import_image": {},
            },
        ),
        (
            [
                {"ImportImageTasks": describe_import_image_tasks},
            ],
            {"changed": True, "import_image": expected_result},
        ),
    ],
)
def test_present_check_mode(client, module, paginate, side_effect, expected_result):
    paginate.build_full_result.side_effect = side_effect
    module.exit_json.side_effect = SystemExit(1)

    with patch(utils + ".helper_describe_import_image_tasks", return_value=paginate):
        with pytest.raises(SystemExit):
            ec2_import_image.absent(client, module)

    module.exit_json.assert_called_with(**expected_result)


@patch(module_name_info + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_import_image_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)
