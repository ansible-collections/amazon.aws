# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloud_config_aws
short_description: Generate testing variable (resource_prefix, tiny_prefix and aws credentials)
description:
  - This module is used to generate resource_prefix and tiny_prefix same as ansible-test does.
  - It also read cloud-config-aws-*.ini file with to inject aws credentials into test environment.
path:
    description:
      - The path to the root of the test directory.
    required: true
    type: str
author:
  - "Aubin Bikouo (@abikouo)"
"""

import configparser
import os
import platform
import random
import re
import uuid
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule


def ensure_test_is_not_using_personal_credentials(module: AnsibleModule) -> None:
    """Ensure local directory '~/.aws' does not exist"""
    aws_config_path = os.path.expanduser("~/.aws")
    if os.path.exists(aws_config_path):
        module.fail_json(msg='Rename "%s" to isolate tests.' % aws_config_path)


def generate_resource_prefix() -> str:
    """Return a resource prefix."""
    prefix = "ansible-test-%d-%s" % (
        random.randint(10000000, 99999999),
        platform.node().split(".")[0],
    )

    return re.sub(r"[^a-zA-Z0-9]+", "-", prefix)[:63].lower().rstrip("-")


def read_cloud_config_credentials(credentials_file: Path) -> dict[str, str]:
    """Read credentials from any cloud-config-aws-*.ini file found from {path}/tests/integration/cloud-config-aws-nxvxfq6h.ini"""
    content = credentials_file.read_text()

    # interpolation=None avoids errors on '%' characters inside STS tokens
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(content)

    return {section: dict(parser[section]) for section in parser.sections()}


def ansible_test_credentials(module: AnsibleModule) -> dict[str, str]:
    """Run ansible-test integration xxx to generate AWS credentials and save them"""
    collection_root_dir = module.params["path"]
    credentials_file_path = Path(
        os.path.join(collection_root_dir, "tests/integration/cloud-config-aws.ini")
    )
    to_delete = False
    if not credentials_file_path.exists():
        ansible_test_command = [
            "ansible-test",
            "integration",
            "molecule_credentials",
            "--no-temp-workdir",
            "-v",
        ]

        command = " ".join(ansible_test_command)
        rc, stdout, stderr = module.run_command(
            command,
            check_rc=True,
        )
        if rc != 0 or not credentials_file_path.exists():
            module.fail_json(
                msg=f"An error occurred while generating credentials file, the file '{credentials_file_path.resolve()}' does not exist.",
                rc=0,
                stderr=stderr,
                stdout=stdout,
            )
        to_delete = True
    data = read_cloud_config_credentials(credentials_file_path)
    # Delete file, safely ignore if the file doesn't exist
    if to_delete:
        credentials_file_path.unlink(missing_ok=True)
    return data


def main():
    argument_spec = {"path": {"type": "str", "required": True}}

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    ensure_test_is_not_using_personal_credentials(module)
    aws_credentials = ansible_test_credentials(module)
    aws_vars = {
        **aws_credentials["default"],
        "tiny_prefix": uuid.uuid4().hex[0:12],
        "resource_prefix": generate_resource_prefix(),
    }

    module.exit_json(changed=False, aws_vars=aws_vars)


if __name__ == "__main__":
    main()
