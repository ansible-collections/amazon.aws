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
      - Mutually exclusive with parameter I(key_material).
    type: str
    choices:
      - rsa
      - ed25519
    version_added: 3.1.0
notes:
  - Support for I(tags) and I(purge_tags) was added in release 2.1.0.
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
  amazon.aws.ec2_key:
    name: my_keypair

- name: create key pair using provided key_material
  amazon.aws.ec2_key:
    name: my_keypair
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'

- name: create key pair using key_material obtained using 'file' lookup plugin
  amazon.aws.ec2_key:
    name: my_keypair
    key_material: "{{ lookup('file', '/path/to/public_key/id_rsa.pub') }}"

- name: Create ED25519 key pair
  amazon.aws.ec2_key:
    name: my_keypair
    key_type: ed25519

# try creating a key pair with the name of an already existing keypair
# but don't overwrite it even if the key is different (force=false)
- name: try creating a key pair with name of an already existing keypair
  amazon.aws.ec2_key:
    name: my_existing_keypair
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'
    force: false

- name: remove key pair by name
  amazon.aws.ec2_key:
    name: my_keypair
    state: absent
"""

RETURN = r"""
changed:
  description: whether a keypair was created/deleted
  returned: always
  type: bool
  sample: true
msg:
  description: short message describing the action taken
  returned: always
  type: str
  sample: key pair created
key:
  description: details of the keypair (this is set to null when state is absent)
  returned: always
  type: complex
  contains:
    fingerprint:
      description: fingerprint of the key
      returned: when state is present
      type: str
      sample: 'b0:22:49:61:d9:44:9d:0c:7e:ac:8a:32:93:21:6c:e8:fb:59:62:43'
    name:
      description: name of the keypair
      returned: when state is present
      type: str
      sample: my_keypair
    id:
      description: id of the keypair
      returned: when state is present
      type: str
      sample: key-123456789abc
    tags:
      description: a dictionary representing the tags attached to the key pair
      returned: when state is present
      type: dict
      sample: '{"my_key": "my value"}'
    private_key:
      description: private key of a newly created keypair
      returned: when a new keypair is created by AWS (key_material is not provided)
      type: str
      sample: '-----BEGIN RSA PRIVATE KEY-----
        MIIEowIBAAKC...
        -----END RSA PRIVATE KEY-----'
    type:
      description: type of a newly created keypair
      returned: when a new keypair is created by AWS
      type: str
      sample: rsa
      version_added: 3.1.0
"""

import uuid

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils._text import to_bytes

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


class Ec2KeyFailure(Exception):
    def __init__(self, message=None, original_e=None):
        super().__init__(message)
        self.original_e = original_e
        self.message = message


def _import_key_pair(ec2_client, name, key_material, tag_spec=None):
    params = {"KeyName": name, "PublicKeyMaterial": to_bytes(key_material), "TagSpecifications": tag_spec}

    params = scrub_none_parameters(params)

    try:
        key = ec2_client.import_key_pair(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as err:
        raise Ec2KeyFailure(err, "error importing key")
    return key


def extract_key_data(key, key_type=None):
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
        key = ec2_client.describe_key_pairs(aws_retry=True, KeyNames=[name])
    except is_boto3_error_code("InvalidKeyPair.NotFound"):
        return None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as err:  # pylint: disable=duplicate-except
        raise Ec2KeyFailure(err, "error finding keypair")
    except IndexError:
        key = None

    return key["KeyPairs"][0]


def _create_key_pair(ec2_client, name, tag_spec, key_type):
    params = {
        "KeyName": name,
        "TagSpecifications": tag_spec,
        "KeyType": key_type,
    }

    params = scrub_none_parameters(params)

    try:
        key = ec2_client.create_key_pair(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as err:
        raise Ec2KeyFailure(err, "error creating key")
    return key


def create_new_key_pair(ec2_client, name, key_material, key_type, tags, check_mode):
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
    key_data = extract_key_data(key, key_type)

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


def update_key_pair_by_key_type(check_mode, ec2_client, name, key_type, tag_spec):
    if check_mode:
        return {"changed": True, "key": None, "msg": "key pair updated"}
    else:
        delete_key_pair(check_mode, ec2_client, name, finish_task=False)
        key = _create_key_pair(ec2_client, name, tag_spec, key_type)
        key_data = extract_key_data(key, key_type)
        return {"changed": True, "key": key_data, "msg": "key pair updated"}


def _delete_key_pair(ec2_client, key_name):
    try:
        ec2_client.delete_key_pair(aws_retry=True, KeyName=key_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as err:
        raise Ec2KeyFailure(err, "error deleting key")


def delete_key_pair(check_mode, ec2_client, name, finish_task=True):
    key = find_key_pair(ec2_client, name)

    if key and check_mode:
        result = {"changed": True, "key": None, "msg": "key deleted"}
    elif not key:
        result = {"key": None, "msg": "key did not exist"}
    else:
        _delete_key_pair(ec2_client, name)
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
    if key_material and force:
        result = update_key_pair_by_key_material(check_mode, ec2_client, name, key, key_material, tag_spec)
    elif key_type and key_type != key["KeyType"]:
        result = update_key_pair_by_key_type(check_mode, ec2_client, name, key_type, tag_spec)
    else:
        changed = False
        changed |= ensure_ec2_tags(ec2_client, module, key["KeyPairId"], tags=tags, purge_tags=purge_tags)
        key = find_key_pair(ec2_client, name)
        key_data = extract_key_data(key)
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
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, mutually_exclusive=[["key_material", "key_type"]], supports_check_mode=True
    )

    ec2_client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    name = module.params["name"]
    state = module.params.get("state")
    key_material = module.params.get("key_material")
    key_type = module.params.get("key_type")
    tags = module.params.get("tags")

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
                result = create_new_key_pair(ec2_client, name, key_material, key_type, tags, module.check_mode)

    except Ec2KeyFailure as e:
        if e.original_e:
            module.fail_json_aws(e.original_e, e.message)
        else:
            module.fail_json(e.message)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
