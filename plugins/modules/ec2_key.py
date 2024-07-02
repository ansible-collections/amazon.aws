#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_key
version_added: 1.0.0
short_description: Create or delete an EC2 key pair
description:
  - Create or delete an EC2 key pair.
options:
  name:
    description:
      - Name of the key pair.
    required: true
    type: str
  key_material:
    description:
      - Public key material.
    required: false
    type: str
  force:
    description:
      - Force overwrite of already existing key pair if key has changed.
    required: false
    default: true
    type: bool
  state:
    description:
      - Create or delete keypair.
    required: false
    choices: [ present, absent ]
    default: 'present'
    type: str
  key_type:
    description:
      - The type of key pair to create.
      - Note that ED25519 keys are not supported for Windows instances,
        EC2 Instance Connect, and EC2 Serial Console.
      - By default Amazon will create an RSA key.
      - Mutually exclusive with parameter O(key_material).
    type: str
    choices:
      - rsa
      - ed25519
    version_added: 3.1.0
  file_name:
    description:
      - Name of the file where the generated private key will be saved.
      - When provided, the RV(key.private_key) attribute will be removed from the return value.
      - The file is written out on the 'host' side rather than the 'controller' side.
      - Ignored when O(state=absent) or O(key_material) is provided.
    type: path
    version_added: 6.4.0
notes:
  - Support for O(tags) and O(purge_tags) was added in release 2.1.0.
  - For security reasons, this module should be used with B(no_log=true) and (register) functionalities
    when creating new key pair without providing O(key_material).
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3

author:
  - "Vincent Viallet (@zbal)"
  - "Prasad Katti (@prasadkatti)"
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a new EC2 key pair, returns generated private key
  # use no_log to avoid private key being displayed into output
  amazon.aws.ec2_key:
    name: my_keypair
  no_log: true
  register: aws_ec2_key_pair

- name: create key pair using provided key_material
  amazon.aws.ec2_key:
    name: my_keypair
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'

- name: create key pair using key_material obtained using 'file' lookup plugin
  amazon.aws.ec2_key:
    name: my_keypair
    key_material: "{{ lookup('file', '/path/to/public_key/id_rsa.pub') }}"

- name: Create ED25519 key pair and save private key into a file
  amazon.aws.ec2_key:
    name: my_keypair
    key_type: ed25519
    file_name: /tmp/aws_ssh_rsa

# try creating a key pair with the name of an already existing keypair
# but don't overwrite it even if the key is different (force=false)
- name: try creating a key pair with name of an already existing keypair
  amazon.aws.ec2_key:
    name: my_existing_keypair
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'
    force: false

- name: remove key pair from AWS by name
  amazon.aws.ec2_key:
    name: my_keypair
    state: absent
"""

RETURN = r"""
changed:
  description: Whether a keypair was created/deleted.
  returned: always
  type: bool
  sample: true
msg:
  description: Short message describing the action taken.
  returned: always
  type: str
  sample: key pair created
key:
  description: Details of the keypair (this is set to null when state is absent).
  returned: always
  type: complex
  contains:
    fingerprint:
      description: Fingerprint of the key.
      returned: when O(state=present)
      type: str
      sample: 'b0:22:49:61:d9:44:9d:0c:7e:ac:8a:32:93:21:6c:e8:fb:59:62:43'
    name:
      description: Name of the keypair.
      returned: when O(state=present)
      type: str
      sample: my_keypair
    id:
      description: Id of the keypair.
      returned: when O(state=present)
      type: str
      sample: key-123456789abc
    tags:
      description: A dictionary representing the tags attached to the key pair.
      returned: when O(state=present)
      type: dict
      sample: '{"my_key": "my value"}'
    private_key:
      description: Private key of a newly created keypair.
      returned: when a new keypair is created by AWS (O(key_material) is not provided) and O(file_name) is not provided.
      type: str
      sample: '-----BEGIN RSA PRIVATE KEY-----
        MIIEowIBAAKC...
        -----END RSA PRIVATE KEY-----'
    type:
      description: Type of a newly created keypair.
      returned: when a new keypair is created by AWS
      type: str
      sample: rsa
      version_added: 3.1.0
"""

import os
import uuid

from ansible.module_utils._text import to_bytes

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_key_pair
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_key_pair as delete_ec2_key_pair
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_key_pairs
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import import_key_pair
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


class Ec2KeyFailure(Exception):
    def __init__(self, message=None, original_e=None):
        super().__init__(message)
        self.original_e = original_e
        self.message = message


def _import_key_pair(ec2_client, name, key_material, tag_spec=None):
    params = {"KeyName": name, "PublicKeyMaterial": to_bytes(key_material), "TagSpecifications": tag_spec}

    params = scrub_none_parameters(params)

    try:
        key = import_key_pair(ec2_client, **params)
    except AnsibleEC2Error as e:
        raise Ec2KeyFailure(e, "error importing key")
    return key


def extract_key_data(key, key_type=None, file_name=None):
    data = {
        "name": key["KeyName"],
        "fingerprint": key["KeyFingerprint"],
        "id": key["KeyPairId"],
        "tags": boto3_tag_list_to_ansible_dict(key.get("Tags") or []),
        # KeyMaterial is returned by create_key_pair, but not by describe_key_pairs
        "private_key": key.get("KeyMaterial"),
        # KeyType is only set by describe_key_pairs
        "type": key.get("KeyType") or key_type,
    }

    # Write the private key to disk and remove it from the return value
    if file_name and data["private_key"] is not None:
        data = _write_private_key(data, file_name)
    return scrub_none_parameters(data)


def get_key_fingerprint(check_mode, ec2_client, key_material):
    """
    EC2's fingerprints are non-trivial to generate, so push this key
    to a temporary name and make ec2 calculate the fingerprint for us.
    http://blog.jbrowne.com/?p=23
    https://forums.aws.amazon.com/thread.jspa?messageID=352828
    """
    # find an unused name
    name_in_use = True
    while name_in_use:
        random_name = "ansible-" + str(uuid.uuid4())
        name_in_use = find_key_pair(ec2_client, random_name)
    temp_key = _import_key_pair(ec2_client, random_name, key_material)
    delete_key_pair(check_mode, ec2_client, random_name, finish_task=False)
    return temp_key["KeyFingerprint"]


def find_key_pair(ec2_client, name):
    try:
        key = describe_key_pairs(ec2_client, KeyNames=[name])
        if not key:
            return None
    except AnsibleEC2Error as e:
        raise Ec2KeyFailure(e, "error finding keypair")
    except IndexError:
        key = None

    return key[0]


def _create_key_pair(ec2_client, name, tag_spec, key_type):
    params = {
        "KeyName": name,
        "TagSpecifications": tag_spec,
        "KeyType": key_type,
    }

    params = scrub_none_parameters(params)

    try:
        key = create_key_pair(ec2_client, **params)
    except AnsibleEC2Error as e:
        raise Ec2KeyFailure(e, "error creating key")
    return key


def _write_private_key(key_data, file_name):
    """
    Write the private key data to the specified file, and remove 'private_key'
    from the ouput. This ensures we don't expose the key data in logs or task output.
    """
    try:
        file = os.open(file_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(file, key_data["private_key"].encode("utf-8"))
        os.close(file)
    except (IOError, OSError) as e:
        raise Ec2KeyFailure(e, "Could not save private key to specified path. Private key is irretrievable.")

    del key_data["private_key"]
    return key_data


def create_new_key_pair(ec2_client, name, key_material, key_type, tags, file_name, check_mode):
    """
    key does not exist, we create new key
    """
    if check_mode:
        return {"changed": True, "key": None, "msg": "key pair created"}

    tag_spec = boto3_tag_specifications(tags, ["key-pair"])
    if key_material:
        key = _import_key_pair(ec2_client, name, key_material, tag_spec)
    else:
        key = _create_key_pair(ec2_client, name, tag_spec, key_type)
    key_data = extract_key_data(key, key_type, file_name)

    result = {"changed": True, "key": key_data, "msg": "key pair created"}
    return result


def update_key_pair_by_key_material(check_mode, ec2_client, name, key, key_material, tag_spec):
    if check_mode:
        return {"changed": True, "key": None, "msg": "key pair updated"}
    new_fingerprint = get_key_fingerprint(check_mode, ec2_client, key_material)
    changed = False
    msg = "key pair already exists"
    if key["KeyFingerprint"] != new_fingerprint:
        delete_key_pair(check_mode, ec2_client, name, finish_task=False)
        key = _import_key_pair(ec2_client, name, key_material, tag_spec)
        msg = "key pair updated"
        changed = True
    key_data = extract_key_data(key)
    return {"changed": changed, "key": key_data, "msg": msg}


def update_key_pair_by_key_type(check_mode, ec2_client, name, key_type, tag_spec, file_name):
    if check_mode:
        return {"changed": True, "key": None, "msg": "key pair updated"}
    else:
        delete_key_pair(check_mode, ec2_client, name, finish_task=False)
        key = _create_key_pair(ec2_client, name, tag_spec, key_type)
        key_data = extract_key_data(key, key_type, file_name)
        return {"changed": True, "key": key_data, "msg": "key pair updated"}


def delete_key_pair(check_mode, ec2_client, name, finish_task=True):
    key = find_key_pair(ec2_client, name)

    if key and check_mode:
        result = {"changed": True, "key": None, "msg": "key deleted"}
    elif not key:
        result = {"key": None, "msg": "key did not exist"}
        return result
    else:
        try:
            delete_ec2_key_pair(ec2_client, name)
        except AnsibleEC2Error as e:
            raise Ec2KeyFailure(e, "error deleting keypair")
        if not finish_task:
            return
        result = {"changed": True, "key": None, "msg": "key deleted"}

    return result


def handle_existing_key_pair_update(module, ec2_client, name, key):
    key_material = module.params.get("key_material")
    force = module.params.get("force")
    key_type = module.params.get("key_type")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    tag_spec = boto3_tag_specifications(tags, ["key-pair"])
    check_mode = module.check_mode
    file_name = module.params.get("file_name")
    if key_material and force:
        result = update_key_pair_by_key_material(check_mode, ec2_client, name, key, key_material, tag_spec)
    elif key_type and key_type != key["KeyType"]:
        result = update_key_pair_by_key_type(check_mode, ec2_client, name, key_type, tag_spec, file_name)
    else:
        changed = False
        changed |= ensure_ec2_tags(ec2_client, module, key["KeyPairId"], tags=tags, purge_tags=purge_tags)
        key = find_key_pair(ec2_client, name)
        key_data = extract_key_data(key, file_name=file_name)
        result = {"changed": changed, "key": key_data, "msg": "key pair already exists"}
    return result


def main():
    argument_spec = dict(
        name=dict(required=True),
        key_material=dict(no_log=False),
        force=dict(type="bool", default=True),
        state=dict(default="present", choices=["present", "absent"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        key_type=dict(type="str", choices=["rsa", "ed25519"]),
        file_name=dict(type="path", required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["key_material", "key_type"]],
        supports_check_mode=True,
    )

    ec2_client = module.client("ec2")

    name = module.params["name"]
    state = module.params.get("state")
    key_material = module.params.get("key_material")
    key_type = module.params.get("key_type")
    tags = module.params.get("tags")
    file_name = module.params.get("file_name")

    result = {}

    try:
        if state == "absent":
            result = delete_key_pair(module.check_mode, ec2_client, name)

        elif state == "present":
            # check if key already exists
            key = find_key_pair(ec2_client, name)
            if key:
                result = handle_existing_key_pair_update(module, ec2_client, name, key)
            else:
                result = create_new_key_pair(
                    ec2_client, name, key_material, key_type, tags, file_name, module.check_mode
                )

    except Ec2KeyFailure as e:
        if e.original_e:
            module.fail_json_aws(e.original_e, e.message)
        else:
            module.fail_json(e.message)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
