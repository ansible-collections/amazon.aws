# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloud_config_aws
short_description: Generate testing variable (resource_prefix, tiny_prefix and aws credentials)
description:
  - This module is used to generate resource_prefix and tiny_prefix same as ansible-test does.
  - It also reads the credentials file written by the C(molecule_credentials) integration test
    target in order to inject aws credentials into test environment.
options:
  path:
    description:
      - The path to the root of the collection.
    required: true
    type: str
author:
  - "Aubin Bikouo (@abikouo)"
"""

EXAMPLES = r"""
- name: Create cloud config configuration data
  cloud_config_aws:
    path: "{{ lookup('ansible.builtin.env', 'MOLECULE_PROJECT_DIRECTORY') }}"
  register: cloud_data
  no_log: true
"""

RETURN = r"""
aws_vars:
  description:
    - The AWS credentials read from the credentials file, plus the generated
      C(tiny_prefix) and C(resource_prefix) test variables.
  returned: success
  type: dict
  sample:
    aws_access_key: "AKIAIOSFODNN7EXAMPLE"
    aws_secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    aws_region: "us-east-1"
    security_token: "FwoGZXIvYXdzEExampleToken"
    tiny_prefix: "cb83ef1c10e5"
    resource_prefix: "ansible-test-12345678-runner"
"""

import configparser
import os
import platform
import random
import re
import uuid
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule

# Deliberately NOT 'tests/integration/cloud-config-aws.ini': that path is where
# ansible-test looks for a *static* cloud config and, when present, it is used
# instead of provisioning fresh credentials. Leaving a molecule-generated file
# there would make every later 'ansible-test integration cloud/aws' run in the
# same checkout reuse expired STS credentials.
CREDENTIALS_RELATIVE_PATH = "tests/integration/molecule-aws-credentials.ini"


def ensure_test_is_not_using_personal_credentials(module: AnsibleModule) -> None:
    """Ensure local directory '~/.aws' does not exist"""
    aws_config_path = os.path.expanduser("~/.aws")
    if os.path.exists(aws_config_path):
        module.fail_json(msg=f'Rename "{aws_config_path}" to isolate tests.')


def generate_resource_prefix() -> str:
    """Return a resource prefix."""
    prefix = f"ansible-test-{random.randint(10000000, 99999999)}-{platform.node().split('.')[0]}"

    return re.sub(r"[^a-zA-Z0-9]+", "-", prefix)[:63].lower().rstrip("-")


def read_cloud_config_credentials(credentials_file: Path) -> dict[str, dict[str, str]]:
    """Read credentials from the ini file written by the molecule_credentials target."""
    content = credentials_file.read_text()

    # interpolation=None avoids errors on '%' characters inside STS tokens
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(content)

    return {section: dict(parser[section]) for section in parser.sections()}


def ansible_test_credentials(module: AnsibleModule) -> dict[str, dict[str, str]]:
    """Run ansible-test integration xxx to generate AWS credentials and save them"""
    collection_root_dir = module.params["path"]
    credentials_file_path = Path(os.path.join(collection_root_dir, CREDENTIALS_RELATIVE_PATH))
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
        # --no-temp-workdir requires the current working directory to be at or
        # below the collection content root, which is not guaranteed for the
        # directory the module process happens to inherit.
        rc, stdout, stderr = module.run_command(command, cwd=collection_root_dir)
        if rc != 0 or not credentials_file_path.exists():
            module.fail_json(
                msg=(
                    "An error occurred while generating credentials file, the file "
                    f"'{credentials_file_path}' does not exist."
                ),
                rc=rc,
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

    # Check mode is not supported: the module provisions real AWS credentials
    # through ansible-test and removes the generated file, so it cannot run
    # without side effects.
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
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
