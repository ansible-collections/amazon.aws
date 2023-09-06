#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: route53_wait
version_added: 6.3.0
short_description: wait for changes in Amazons Route 53 DNS service to propagate
description:
  - When using M(amazon.aws.route53) with I(wait=false), this module allows to wait for the
    module's propagation to finish at a later point of time.
options:
  result:
    aliases:
      - results
    description:
      - The registered result of one or multiple M(amazon.aws.route53) invocations.
    required: true
    type: dict
  wait_timeout:
    description:
      - How long to wait for the changes to be replicated, in seconds.
      - This timeout will be used for every changed result in I(result).
    default: 300
    type: int
  region:
    description:
      - This setting is ignored by the module. It is only present to make it possible to
        have I(region) present in the module default group.
    type: str
author:
  - Felix Fontein (@felixfontein)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.boto3
"""

RETURN = r"""
#
"""

EXAMPLES = r"""
# Example when using a single route53 invocation:

- name: Add new.foo.com as an A record with 3 IPs
  amazon.aws.route53:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value:
      - 1.1.1.1
      - 2.2.2.2
      - 3.3.3.3
  register: module_result

# do something else

- name: Wait for the changes of the above route53 invocation to propagate
  community.aws.route53_wait:
    result: "{{ module_result }}"

#########################################################################
# Example when using a loop over amazon.aws.route53:

- name: Add various A records
  amazon.aws.route53:
    state: present
    zone: foo.com
    record: "{{ item.record }}"
    type: A
    ttl: 300
    value: "{{ item.value }}"
  loop:
    - record: new.foo.com
      value: 1.1.1.1
    - record: foo.foo.com
      value: 2.2.2.2
    - record: bar.foo.com
      value:
        - 3.3.3.3
        - 4.4.4.4
  register: module_results

# do something else

- name: Wait for the changes of the above three route53 invocations to propagate
  community.aws.route53_wait:
    results: "{{ module_results }}"
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule

WAIT_RETRY = 5  # how many seconds to wait between propagation status polls


def detect_task_results(results):
    if "results" in results:
        # This must be the registered result of a loop of route53 tasks
        for key in ("changed", "msg", "skipped"):
            if key not in results:
                raise ValueError(f"missing {key} key")
        if not isinstance(results["results"], list):
            raise ValueError("results is present, but not a list")
        for index, result in enumerate(results["results"]):
            if not isinstance(result, dict):
                raise ValueError(f"result {index + 1} is not a dictionary")
            for key in ("changed", "failed", "ansible_loop_var", "invocation"):
                if key not in result:
                    raise ValueError(f"missing {key} key for result {index + 1}")
            yield f" for result #{index + 1}", result
        return
    # This must be a single route53 task
    for key in ("changed", "failed"):
        if key not in results:
            raise ValueError(f"missing {key} key")
    yield "", results


def main():
    argument_spec = dict(
        result=dict(type="dict", required=True, aliases=["results"]),
        wait_timeout=dict(type="int", default=300),
        region=dict(type="str"),  # ignored
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    result_in = module.params["result"]
    wait_timeout_in = module.params.get("wait_timeout")

    changed_results = []
    try:
        for id, result in detect_task_results(result_in):
            if result.get("wait_id"):
                changed_results.append((id, result["wait_id"]))
    except ValueError as exc:
        module.fail_json(
            msg=f"The value passed as result does not seem to be a registered route53 result: {to_native(exc)}"
        )

    # connect to the route53 endpoint
    try:
        route53 = module.client("route53")
    except botocore.exceptions.HTTPClientError as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    for what, wait_id in changed_results:
        try:
            waiter = get_waiter(route53, "resource_record_sets_changed")
            waiter.wait(
                Id=wait_id,
                WaiterConfig=dict(
                    Delay=WAIT_RETRY,
                    MaxAttempts=wait_timeout_in // WAIT_RETRY,
                ),
            )
        except botocore.exceptions.WaiterError as e:
            module.fail_json_aws(e, msg=f"Timeout waiting for resource records changes{what} to be applied")
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to update records")
        except Exception as e:
            module.fail_json(msg=f"Unhandled exception. ({to_native(e)})")

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
