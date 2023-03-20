#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: mq_broker
version_added: 6.0.0
short_description: MQ broker management
description:
  - Create/update/delete a broker.
  - Reboot a broker.
author:
  - FCO (@fotto)
options:
  broker_name:
    description:
      - The Name of the MQ broker to work on.
    type: str
    required: true
  state:
    description:
      - "C(present): Create/update broker."
      - "C(absent): Delete broker."
      - "C(restarted): Reboot broker."
    choices: [ 'present', 'absent', 'restarted' ]
    default: present
    type: str
  deployment_mode:
    description:
      - Set broker deployment type.
      - Can be used only during creation.
      - Defaults to C(SINGLE_INSTANCE).
    choices: [ 'SINGLE_INSTANCE', 'ACTIVE_STANDBY_MULTI_AZ', 'CLUSTER_MULTI_AZ' ]
    type: str
  use_aws_owned_key:
    description:
      - Must be set to C(false) if I(kms_key_id) is provided as well.
      - Can be used only during creation.
      - Defaults to C(true).
    type: bool
  kms_key_id:
    description:
      - Use referenced key to encrypt broker data at rest.
      - Can be used only during creation.
    type: str
  engine_type:
    description:
      - Set broker engine type.
      - Can be used only during creation.
      - Defaults to C(ACTIVEMQ).
    choices: [ 'ACTIVEMQ', 'RABBITMQ' ]
    type: str
  maintenance_window_start_time:
    description:
      - Set maintenance window for automatic minor upgrades.
      - Can be used only during creation.
      - Not providing any value means "no maintenance window".
    type: dict
  publicly_accessible:
    description:
      - Allow/disallow public access.
      - Can be used only during creation.
      - Defaults to C(false).
    type: bool
  storage_type:
    description:
      - Set underlying storage type.
      - Can be used only during creation.
      - Defaults to C(EFS).
    choices: [ 'EBS', 'EFS' ]
    type: str
  subnet_ids:
    description:
      - Defines where deploy broker instances to.
      - Minimum required number depends on deployment type.
      - Can be used only during creation.
    type: list
    elements: str
  users:
    description:
      - This parameter allows to use a custom set of initial user(s).
      - M(community.aws.mq_user) is the preferred way to manage (local) users
        however a broker cannot be created without any user.
      - If nothing is specified a default C(admin) user will be created along with brokers.
      - Can be used only during creation.  Use M(community.aws.mq_user) module for updates.
    type: list
    elements: dict
  tags:
    description:
      - Tag newly created brokers.
      - Can be used only during creation.
    type: dict
  authentication_strategy:
    description: Choose between locally and remotely managed users.
    choices: [ 'SIMPLE', 'LDAP' ]
    type: str
  auto_minor_version_upgrade:
    description: Allow/disallow automatic minor version upgrades.
    type: bool
    default: true
  engine_version:
    description:
      - Set engine version of broker.
      - The special value C(latest) will pick the latest available version.
      - The special value C(latest) is ignored on update.
    type: str
  host_instance_type:
    description: Instance type of broker instances.
    type: str
  enable_audit_log:
    description: Enable/disable to push audit logs to AWS CloudWatch.
    type: bool
    default: false
  enable_general_log:
    description: Enable/disable to push general logs to AWS CloudWatch.
    type: bool
    default: false
  security_groups:
    description:
      - Associate security groups with broker.
      - At least one must be provided during creation.
    type: list
    elements: str

extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.modules
  - amazon.aws.region.modules
"""


EXAMPLES = r"""
- name: create broker (if missing) with minimal required parameters
  amazon.aws.mq_broker:
    broker_name: "{{ broker_name }}"
    security_groups:
      - sg_xxxxxxx
    subnet_ids:
      - subnet_xxx
      - subnet_yyy
    register: result
- set_fact:
    broker_id: "{{ result.broker['BrokerId'] }}"
- name: use mq_broker_info to wait until broker is ready
  amazon.aws.mq_broker_info:
    broker_id: "{{ broker_id }}"
  register: result
  until: "result.broker['BrokerState'] == 'RUNNING'"
  retries: 15
  delay:   60
- name: create or update broker with almost all parameter set including credentials
  amazon.aws.mq_broker:
    broker_name: "my_broker_2"
    state: present
    deployment_mode: 'ACTIVE_STANDBY_MULTI_AZ'
    use_aws_owned_key: false
    kms_key_id: 'my-precreted-key-id'
    engine_type: 'ACTIVEMQ'
    maintenance_window_start_time:
      DayOfWeek: 'MONDAY'
      TimeOfDay: '03:15'
      TimeZone: 'Europe/Berlin'
    publicly_accessible: true
    storage_type: 'EFS'
    security_groups:
      - sg_xxxxxxx
    subnet_ids:
      - subnet_xxx
      - subnet_yyy
    users:
    - Username: 'initial-user'
      Password': 'plain-text-password'
      ConsoleAccess: true
    tags:
    - env: Test
      creator: ansible
    authentication_strategy: 'SIMPLE'
    auto_minor_version_upgrade: true
    engine_version: "5.15.13"
    host_instance_type: 'mq.t3.micro'
    enable_audit_log: true
    enable_general_log: true
- name: reboot a broker
  amazon.aws.mq_broker:
    broker_name: "my_broker_2"
    state: restarted
- name: delete a broker
  amazon.aws.mq_broker:
    broker_name: "my_broker_2"
    state: absent
"""

RETURN = r"""
broker:
  description:
    - "All API responses are converted to snake yaml except 'Tags'"
    - "'state=present': API response of create_broker() or update_broker() call"
    - "'state=absent': result of describe_broker() call before delete_broker() is triggerd"
    - "'state=restarted': result of describe_broker() after reboot has been triggered"
  type: dict
  returned: success
"""

try:
    import botocore
except ImportError:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


PARAMS_MAP = {
    "authentication_strategy": "AuthenticationStrategy",
    "auto_minor_version_upgrade": "AutoMinorVersionUpgrade",
    "broker_name": "BrokerName",
    "deployment_mode": "DeploymentMode",
    "use_aws_owned_key": "EncryptionOptions/UseAwsOwnedKey",
    "kms_key_id": "EncryptionOptions/KmsKeyId",
    "engine_type": "EngineType",
    "engine_version": "EngineVersion",
    "host_instance_type": "HostInstanceType",
    "enable_audit_log": "Logs/Audit",
    "enable_general_log": "Logs/General",
    "maintenance_window_start_time": "MaintenanceWindowStartTime",
    "publicly_accessible": "PubliclyAccessible",
    "security_groups": "SecurityGroups",
    "storage_type": "StorageType",
    "subnet_ids": "SubnetIds",
    "users": "Users",
}


DEFAULTS = {
    "authentication_strategy": "SIMPLE",
    "auto_minor_version_upgrade": False,
    "deployment_mode": "SINGLE_INSTANCE",
    "use_aws_owned_key": True,
    "engine_type": "ACTIVEMQ",
    "engine_version": "latest",
    "host_instance_type": "mq.t3.micro",
    "enable_audit_log": False,
    "enable_general_log": False,
    "publicly_accessible": False,
    "storage_type": "EFS",
}

CREATE_ONLY_PARAMS = [
    "deployment_mode",
    "use_aws_owned_key",
    "kms_key_id",
    "engine_type",
    "maintenance_window_start_time",
    "publicly_accessible",
    "storage_type",
    "subnet_ids",
    "users",
    "tags",
]


def _set_kwarg(kwargs, key, value):
    mapped_key = PARAMS_MAP[key]
    if "/" in mapped_key:
        key_list = mapped_key.split("/")
        key_list.reverse()
    else:
        key_list = [mapped_key]
    data = kwargs
    while len(key_list) > 1:
        this_key = key_list.pop()
        if this_key not in data:
            data[this_key] = {}
        #
        data = data[this_key]
    data[key_list[0]] = value


def _fill_kwargs(module, apply_defaults=True, ignore_create_params=False):
    kwargs = {}
    if apply_defaults:
        for p_name, p_value in DEFAULTS.items():
            _set_kwarg(kwargs, p_name, p_value)
    for p_name in module.params:
        if ignore_create_params and p_name in CREATE_ONLY_PARAMS:
            # silently ignore CREATE_ONLY_PARAMS on update to
            # make playbooks idempotent
            continue
        if p_name in PARAMS_MAP and module.params[p_name] is not None:
            _set_kwarg(kwargs, p_name, module.params[p_name])
        else:
            # ignore
            pass
    return kwargs


def __list_needs_change(current, desired):
    if len(current) != len(desired):
        return True
    # equal length:
    c_sorted = sorted(current)
    d_sorted = sorted(desired)
    for index, value in enumerate(current):
        if value != desired[index]:
            return True
    #
    return False


def __dict_needs_change(current, desired):
    # values contained in 'current' but not specified in 'desired' are ignored
    # value contained in 'desired' but not in 'current' (unsupported attributes) are ignored
    for key in desired:
        if key in current:
            if desired[key] != current[key]:
                return True
    #
    return False


def _needs_change(current, desired):
    needs_change = False
    for key in desired:
        current_value = current[key]
        desired_value = desired[key]
        if isinstance(current_value, (int, str, bool)):
            if current_value != desired_value:
                needs_change = True
                break
        elif isinstance(current_value, list):
            # assumption: all 'list' type settings we allow changes for have scalar values
            if __list_needs_change(current_value, desired_value):
                needs_change = True
                break
        elif isinstance(current_value, dict):
            # assumption: all 'dict' type settings we allow changes for have scalar values
            if __dict_needs_change(current_value, desired_value):
                needs_change = True
                break
        else:
            # unexpected type
            needs_change = True
            break
    #
    return needs_change


def get_latest_engine_version(conn, module, engine_type):
    try:
        response = conn.describe_broker_engine_types(EngineType=engine_type)
        return response["BrokerEngineTypes"][0]["EngineVersions"][0]["Name"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list engine versions")


def get_broker_id(conn, module):
    try:
        broker_name = module.params["broker_name"]
        broker_id = None
        response = conn.list_brokers(MaxResults=100)
        for broker in response["BrokerSummaries"]:
            if broker["BrokerName"] == broker_name:
                broker_id = broker["BrokerId"]
                break
        return broker_id
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list broker brokers.")


def get_broker_info(conn, module, broker_id):
    try:
        return conn.describe_broker(BrokerId=broker_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get broker details.")


def reboot_broker(conn, module, broker_id):
    try:
        return conn.reboot_broker(BrokerId=broker_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't reboot broker.")


def delete_broker(conn, module, broker_id):
    try:
        return conn.delete_broker(BrokerId=broker_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete broker.")


def create_broker(conn, module):
    kwargs = _fill_kwargs(module)
    if "EngineVersion" in kwargs and kwargs["EngineVersion"] == "latest":
        kwargs["EngineVersion"] = get_latest_engine_version(conn, module, kwargs["EngineType"])
    if kwargs["AuthenticationStrategy"] == "LDAP":
        module.fail_json(msg="'AuthenticationStrategy=LDAP' not supported, yet")
    if "Users" not in kwargs:
        # add some stupid default (cannot create broker without any users)
        kwargs["Users"] = [{"Username": "admin", "Password": "adminPassword", "ConsoleAccess": True, "Groups": []}]
    if "EncryptionOptions" in kwargs and "UseAwsOwnedKey" in kwargs["EncryptionOptions"]:
        kwargs["EncryptionOptions"]["UseAwsOwnedKey"] = False
    #
    if "SecurityGroups" not in kwargs or len(kwargs["SecurityGroups"]) == 0:
        module.fail_json(msg="At least one security group must be specified on broker creation")
    #
    changed = True
    result = conn.create_broker(**kwargs)
    #
    return {"broker": camel_dict_to_snake_dict(result, ignore_list=["Tags"]), "changed": changed}


def update_broker(conn, module, broker_id):
    kwargs = _fill_kwargs(module, apply_defaults=False, ignore_create_params=True)
    # replace name with id
    broker_name = kwargs["BrokerName"]
    del kwargs["BrokerName"]
    kwargs["BrokerId"] = broker_id
    # get current state for comparison:
    api_result = get_broker_info(conn, module, broker_id)
    if api_result["BrokerState"] != "RUNNING":
        module.fail_json(
            msg=f"Cannot trigger update while broker ({broker_id}) is in state {api_result['BrokerState']}",
        )
    # engine version of 'latest' is taken as "keep current one"
    # i.e. do not request upgrade on playbook rerun
    if "EngineVersion" in kwargs and kwargs["EngineVersion"] == "latest":
        kwargs["EngineVersion"] = api_result["EngineVersion"]
    result = {"broker_id": broker_id, "broker_name": broker_name}
    changed = False
    if _needs_change(api_result, kwargs):
        changed = True
        if not module.check_mode:
            api_result = conn.update_broker(**kwargs)
        #
    #
    return {"broker": result, "changed": changed}


def ensure_absent(conn, module):
    result = {"broker_name": module.params["broker_name"], "broker_id": None}
    if module.check_mode:
        return {"broker": camel_dict_to_snake_dict(result, ignore_list=["Tags"]), "changed": True}
    broker_id = get_broker_id(conn, module)
    result["broker_id"] = broker_id

    if not broker_id:
        # silently ignore delete of unknown broker (to make it idempotent)
        return {"broker": result, "changed": False}

    try:
        # check for pending delete (small race condition possible here
        api_result = get_broker_info(conn, module, broker_id)
        if api_result["BrokerState"] == "DELETION_IN_PROGRESS":
            return {"broker": result, "changed": False}
        delete_broker(conn, module, broker_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    return {"broker": result, "changed": True}


def ensure_present(conn, module):
    if module.check_mode:
        return {"broker": {"broker_arn": "fakeArn", "broker_id": "fakeId"}, "changed": True}

    broker_id = get_broker_id(conn, module)
    if broker_id:
        return update_broker(conn, module, broker_id)

    return create_broker(conn, module)


def main():
    argument_spec = dict(
        broker_name=dict(required=True, type="str"),
        state=dict(default="present", choices=["present", "absent", "restarted"]),
        # parameters only allowed on create
        deployment_mode=dict(choices=["SINGLE_INSTANCE", "ACTIVE_STANDBY_MULTI_AZ", "CLUSTER_MULTI_AZ"]),
        use_aws_owned_key=dict(type="bool"),
        kms_key_id=dict(type="str"),
        engine_type=dict(choices=["ACTIVEMQ", "RABBITMQ"], type="str"),
        maintenance_window_start_time=dict(type="dict"),
        publicly_accessible=dict(type="bool"),
        storage_type=dict(choices=["EBS", "EFS"]),
        subnet_ids=dict(type="list", elements="str"),
        users=dict(type="list", elements="dict"),
        tags=dict(type="dict"),
        # parameters allowed on update as well
        authentication_strategy=dict(choices=["SIMPLE", "LDAP"]),
        auto_minor_version_upgrade=dict(default=True, type="bool"),
        engine_version=dict(type="str"),
        host_instance_type=dict(type="str"),
        enable_audit_log=dict(default=False, type="bool"),
        enable_general_log=dict(default=False, type="bool"),
        security_groups=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("mq")

    if module.params["state"] == "present":
        try:
            compound_result = ensure_present(connection, module)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        #
        module.exit_json(**compound_result)

    if module.params["state"] == "absent":
        try:
            compound_result = ensure_absent(connection, module)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        #
        module.exit_json(**compound_result)

    if module.params["state"] == "restarted":
        broker_id = get_broker_id(connection, module)
        if module.check_mode:
            module.exit_json(broker={"broker_id": broker_id if broker_id else "fakeId"}, changed=True)
        if not broker_id:
            module.fail_json(
                msg="Cannot find broker with name {module.params['broker_name']}.",
            )
        try:
            changed = True
            if not module.check_mode:
                reboot_broker(connection, module, broker_id)
            #
            result = get_broker_info(connection, module, broker_id)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        module.exit_json(broker=result, changed=changed)


if __name__ == "__main__":
    main()
