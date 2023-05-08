#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: glue_job
version_added: 1.0.0
short_description: Manage an AWS Glue job
description:
  - Manage an AWS Glue job. See U(https://aws.amazon.com/glue/) for details.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_glue_job).
    The usage did not change.
author:
  - "Rob White (@wimnat)"
  - "Vijayanand Sharma (@vijayanandsharma)"
options:
  allocated_capacity:
    description:
      - The number of AWS Glue data processing units (DPUs) to allocate to this Job. From 2 to 100 DPUs
        can be allocated; the default is 10. A DPU is a relative measure of processing power that consists
        of 4 vCPUs of compute capacity and 16 GB of memory.
    type: int
  command_name:
    description:
      - The name of the job command. This must be 'glueetl'.
    default: glueetl
    type: str
  command_python_version:
    description:
      - Python version being used to execute a Python shell job.
      - AWS currently supports C('2') or C('3').
    type: str
    version_added: 2.2.0
  command_script_location:
    description:
      - The S3 path to a script that executes a job.
      - Required when I(state=present).
    type: str
  connections:
    description:
      - A list of Glue connections used for this job.
    type: list
    elements: str
  default_arguments:
    description:
      - A dict of default arguments for this job.  You can specify arguments here that your own job-execution
        script consumes, as well as arguments that AWS Glue itself consumes.
    type: dict
  description:
    description:
      - Description of the job being defined.
    type: str
  glue_version:
    description:
      - Glue version determines the versions of Apache Spark and Python that AWS Glue supports.
    type: str
    version_added: 1.5.0
  max_concurrent_runs:
    description:
      - The maximum number of concurrent runs allowed for the job. The default is 1. An error is returned when
        this threshold is reached. The maximum value you can specify is controlled by a service limit.
    type: int
  max_retries:
    description:
      -  The maximum number of times to retry this job if it fails.
    type: int
  name:
    description:
      - The name you assign to this job definition. It must be unique in your account.
    required: true
    type: str
  number_of_workers:
    description:
      - The number of workers of a defined workerType that are allocated when a job runs.
    type: int
    version_added: 1.5.0
  role:
    description:
      - The name or ARN of the IAM role associated with this job.
      - Required when I(state=present).
    type: str
  state:
    description:
      - Create or delete the AWS Glue job.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  timeout:
    description:
      - The job timeout in minutes.
    type: int
  worker_type:
    description:
      - The type of predefined worker that is allocated when a job runs.
    choices: [ 'Standard', 'G.1X', 'G.2X' ]
    type: str
    version_added: 1.5.0
notes:
  - Support for I(tags) and I(purge_tags) was added in release 2.2.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an AWS Glue job
- community.aws.glue_job:
    command_script_location: "s3://s3bucket/script.py"
    default_arguments:
      "--extra-py-files": s3://s3bucket/script-package.zip
      "--TempDir": "s3://s3bucket/temp/"
    name: my-glue-job
    role: my-iam-role
    state: present

# Delete an AWS Glue job
- community.aws.glue_job:
    name: my-glue-job
    state: absent
"""

RETURN = r"""
allocated_capacity:
    description: The number of AWS Glue data processing units (DPUs) allocated to runs of this job. From 2 to
                 100 DPUs can be allocated; the default is 10. A DPU is a relative measure of processing power
                 that consists of 4 vCPUs of compute capacity and 16 GB of memory.
    returned: when state is present
    type: int
    sample: 10
command:
    description: The JobCommand that executes this job.
    returned: when state is present
    type: complex
    contains:
        name:
            description: The name of the job command.
            returned: when state is present
            type: str
            sample: glueetl
        script_location:
            description: Specifies the S3 path to a script that executes a job.
            returned: when state is present
            type: str
            sample: mybucket/myscript.py
        python_version:
            description: Specifies the Python version.
            returned: when state is present
            type: str
            sample: 3
connections:
    description: The connections used for this job.
    returned: when state is present
    type: dict
    sample: "{ Connections: [ 'list', 'of', 'connections' ] }"
created_on:
    description: The time and date that this job definition was created.
    returned: when state is present
    type: str
    sample: "2018-04-21T05:19:58.326000+00:00"
default_arguments:
    description: The default arguments for this job, specified as name-value pairs.
    returned: when state is present
    type: dict
    sample: "{ 'mykey1': 'myvalue1' }"
description:
    description: Description of the job being defined.
    returned: when state is present
    type: str
    sample: My first Glue job
glue_version:
    description: Glue version.
    returned: when state is present
    type: str
    sample: 2.0
job_name:
    description: The name of the AWS Glue job.
    returned: always
    type: str
    sample: my-glue-job
execution_property:
    description: An ExecutionProperty specifying the maximum number of concurrent runs allowed for this job.
    returned: always
    type: complex
    contains:
        max_concurrent_runs:
            description: The maximum number of concurrent runs allowed for the job. The default is 1. An error is
                         returned when this threshold is reached. The maximum value you can specify is controlled by
                         a service limit.
            returned: when state is present
            type: int
            sample: 1
last_modified_on:
    description: The last point in time when this job definition was modified.
    returned: when state is present
    type: str
    sample: "2018-04-21T05:19:58.326000+00:00"
max_retries:
    description: The maximum number of times to retry this job after a JobRun fails.
    returned: when state is present
    type: int
    sample: 5
name:
    description: The name assigned to this job definition.
    returned: when state is present
    type: str
    sample: my-glue-job
role:
    description: The name or ARN of the IAM role associated with this job.
    returned: when state is present
    type: str
    sample: my-iam-role
timeout:
    description: The job timeout in minutes.
    returned: when state is present
    type: int
    sample: 300
"""

import copy

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_aws_account_info
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def _get_glue_job(connection, module, glue_job_name):
    """
    Get an AWS Glue job based on name. If not found, return None.

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_job_name: Name of Glue job to get
    :return: boto3 Glue job dict or None if not found
    """
    try:
        return connection.get_job(aws_retry=True, JobName=glue_job_name)["Job"]
    except is_boto3_error_code("EntityNotFoundException"):
        return None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


def _compare_glue_job_params(user_params, current_params):
    """
    Compare Glue job params. If there is a difference, return True immediately else return False

    :param user_params: the Glue job parameters passed by the user
    :param current_params: the Glue job parameters currently configured
    :return: True if any parameter is mismatched else False
    """
    # Weirdly, boto3 doesn't return some keys if the value is empty e.g. Description
    # To counter this, add the key if it's missing with a blank value

    if "Description" not in current_params:
        current_params["Description"] = ""
    if "DefaultArguments" not in current_params:
        current_params["DefaultArguments"] = dict()

    if "AllocatedCapacity" in user_params and user_params["AllocatedCapacity"] != current_params["AllocatedCapacity"]:
        return True
    if "Command" in user_params:
        if user_params["Command"]["ScriptLocation"] != current_params["Command"]["ScriptLocation"]:
            return True
        if user_params["Command"]["PythonVersion"] != current_params["Command"]["PythonVersion"]:
            return True
    if "Connections" in user_params and user_params["Connections"] != current_params["Connections"]:
        return True
    if "DefaultArguments" in user_params and user_params["DefaultArguments"] != current_params["DefaultArguments"]:
        return True
    if "Description" in user_params and user_params["Description"] != current_params["Description"]:
        return True
    if (
        "ExecutionProperty" in user_params
        and user_params["ExecutionProperty"]["MaxConcurrentRuns"]
        != current_params["ExecutionProperty"]["MaxConcurrentRuns"]
    ):
        return True
    if "GlueVersion" in user_params and user_params["GlueVersion"] != current_params["GlueVersion"]:
        return True
    if "MaxRetries" in user_params and user_params["MaxRetries"] != current_params["MaxRetries"]:
        return True
    if "Role" in user_params and user_params["Role"] != current_params["Role"]:
        return True
    if "Timeout" in user_params and user_params["Timeout"] != current_params["Timeout"]:
        return True
    if "GlueVersion" in user_params and user_params["GlueVersion"] != current_params["GlueVersion"]:
        return True
    if "WorkerType" in user_params and user_params["WorkerType"] != current_params["WorkerType"]:
        return True
    if "NumberOfWorkers" in user_params and user_params["NumberOfWorkers"] != current_params["NumberOfWorkers"]:
        return True

    return False


def ensure_tags(connection, module, glue_job):
    changed = False

    if module.params.get("tags") is None:
        return False

    account_id, partition = get_aws_account_info(module)
    arn = f"arn:{partition}:glue:{module.region}:{account_id}:job/{module.params.get('name')}"

    try:
        existing_tags = connection.get_tags(aws_retry=True, ResourceArn=arn).get("Tags", {})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if module.check_mode:
            existing_tags = {}
        else:
            module.fail_json_aws(e, msg=f"Unable to get tags for Glue job {module.params.get('name')}")

    tags_to_add, tags_to_remove = compare_aws_tags(
        existing_tags, module.params.get("tags"), module.params.get("purge_tags")
    )

    if tags_to_remove:
        changed = True
        if not module.check_mode:
            try:
                connection.untag_resource(aws_retry=True, ResourceArn=arn, TagsToRemove=tags_to_remove)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Glue job {module.params.get('name')}")

    if tags_to_add:
        changed = True
        if not module.check_mode:
            try:
                connection.tag_resource(aws_retry=True, ResourceArn=arn, TagsToAdd=tags_to_add)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg=f"Unable to set tags for Glue job {module.params.get('name')}")

    return changed


def create_or_update_glue_job(connection, module, glue_job):
    """
    Create or update an AWS Glue job

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_job: a dict of AWS Glue job parameters or None
    :return:
    """

    changed = False
    params = dict()
    params["Name"] = module.params.get("name")
    params["Role"] = module.params.get("role")
    if module.params.get("allocated_capacity") is not None:
        params["AllocatedCapacity"] = module.params.get("allocated_capacity")
    if module.params.get("command_script_location") is not None:
        params["Command"] = {
            "Name": module.params.get("command_name"),
            "ScriptLocation": module.params.get("command_script_location"),
        }
        if module.params.get("command_python_version") is not None:
            params["Command"]["PythonVersion"] = module.params.get("command_python_version")
    if module.params.get("connections") is not None:
        params["Connections"] = {"Connections": module.params.get("connections")}
    if module.params.get("default_arguments") is not None:
        params["DefaultArguments"] = module.params.get("default_arguments")
    if module.params.get("description") is not None:
        params["Description"] = module.params.get("description")
    if module.params.get("glue_version") is not None:
        params["GlueVersion"] = module.params.get("glue_version")
    if module.params.get("max_concurrent_runs") is not None:
        params["ExecutionProperty"] = {"MaxConcurrentRuns": module.params.get("max_concurrent_runs")}
    if module.params.get("max_retries") is not None:
        params["MaxRetries"] = module.params.get("max_retries")
    if module.params.get("timeout") is not None:
        params["Timeout"] = module.params.get("timeout")
    if module.params.get("glue_version") is not None:
        params["GlueVersion"] = module.params.get("glue_version")
    if module.params.get("worker_type") is not None:
        params["WorkerType"] = module.params.get("worker_type")
    if module.params.get("number_of_workers") is not None:
        params["NumberOfWorkers"] = module.params.get("number_of_workers")

    # If glue_job is not None then check if it needs to be modified, else create it
    if glue_job:
        if _compare_glue_job_params(params, glue_job):
            try:
                # Update job needs slightly modified params
                update_params = {"JobName": params["Name"], "JobUpdate": copy.deepcopy(params)}
                del update_params["JobUpdate"]["Name"]
                if not module.check_mode:
                    connection.update_job(aws_retry=True, **update_params)
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e)
    else:
        try:
            if not module.check_mode:
                connection.create_job(aws_retry=True, **params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e)

    glue_job = _get_glue_job(connection, module, params["Name"])

    changed |= ensure_tags(connection, module, glue_job)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(glue_job or {}, ignore_list=["DefaultArguments"]))


def delete_glue_job(connection, module, glue_job):
    """
    Delete an AWS Glue job

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_job: a dict of AWS Glue job parameters or None
    :return:
    """
    changed = False

    if glue_job:
        try:
            if not module.check_mode:
                connection.delete_job(aws_retry=True, JobName=glue_job["Name"])
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed)


def main():
    argument_spec = dict(
        allocated_capacity=dict(type="int"),
        command_name=dict(type="str", default="glueetl"),
        command_python_version=dict(type="str"),
        command_script_location=dict(type="str"),
        connections=dict(type="list", elements="str"),
        default_arguments=dict(type="dict"),
        description=dict(type="str"),
        glue_version=dict(type="str"),
        max_concurrent_runs=dict(type="int"),
        max_retries=dict(type="int"),
        name=dict(required=True, type="str"),
        number_of_workers=dict(type="int"),
        purge_tags=dict(type="bool", default=True),
        role=dict(type="str"),
        state=dict(required=True, choices=["present", "absent"], type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        timeout=dict(type="int"),
        worker_type=dict(choices=["Standard", "G.1X", "G.2X"], type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[("state", "present", ["role", "command_script_location"])],
        supports_check_mode=True,
    )

    retry_decorator = AWSRetry.jittered_backoff(retries=10)
    connection = module.client("glue", retry_decorator=retry_decorator)

    state = module.params.get("state")

    glue_job = _get_glue_job(connection, module, module.params.get("name"))

    if state == "present":
        create_or_update_glue_job(connection, module, glue_job)
    else:
        delete_glue_job(connection, module, glue_job)


if __name__ == "__main__":
    main()
