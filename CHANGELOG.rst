===========================
community.aws Release Notes
===========================

.. contents:: Topics


v1.3.0
======

Minor Changes
-------------

- aws_caller_info - add AWSRetry decorator to automatically retry on common temporary failures (https://github.com/ansible-collections/amazon.aws/pull/208)
- aws_s3 - Add support for uploading templated content (https://github.com/ansible-collections/amazon.aws/pull/20).
- aws_secret - add "on_missing" and "on_denied" option (https://github.com/ansible-collections/amazon.aws/pull/122).
- ec2_ami - Add retries for ratelimiting related errors (https://github.com/ansible-collections/amazon.aws/pull/195).
- ec2_ami - fixed and streamlined ``max_attempts`` logic when waiting for AMI creation to finish (https://github.com/ansible-collections/amazon.aws/pull/194).
- ec2_ami - increased default ``wait_timeout`` to 1200 seconds (https://github.com/ansible-collections/amazon.aws/pull/194).
- ec2_ami_info - Add retries for ratelimiting related errors (https://github.com/ansible-collections/amazon.aws/pull/195).
- ec2_eni - Improve reliability of the module by adding waiters and performing lookups by ENI ID rather than repeated searches (https://github.com/ansible-collections/amazon.aws/pull/180).
- ec2_eni_info - Improve reliability of the module by adding waiters and performing lookups by ENI ID rather than repeated searches (https://github.com/ansible-collections/amazon.aws/pull/180).
- ec2_group - add AWSRetry decorator to automatically retry on common temporary failures (https://github.com/ansible-collections/amazon.aws/pull/207)
- ec2_group_info - add AWSRetry decorator to automatically retry on common temporary failures (https://github.com/ansible-collections/amazon.aws/pull/207)
- ec2_snapshot_info - add AWSRetry decorator to automatically retry on common temporary failures (https://github.com/ansible-collections/amazon.aws/pull/208)
- ec2_vol - Add automatic retries on AWS rate limit errors (https://github.com/ansible-collections/amazon.aws/pull/199).
- ec2_vol - ported ec2_vol to use boto3 (https://github.com/ansible-collections/amazon.aws/pull/53).
- ec2_vpc_dhcp_option_info - add AWSRetry decorator to automatically retry on common temporary failures (https://github.com/ansible-collections/amazon.aws/pull/208)
- module_utils/core - add helper function ``scrub_none_parameters`` to remove params set to ``None`` (https://github.com/ansible-collections/community.aws/issues/251).
- module_utils/waiters - Add retries to our waiters for the same failure codes that we retry with AWSRetry (https://github.com/ansible-collections/amazon.aws/pull/185)
- s3_bucket - Add support for managing the ``public_access`` settings (https://github.com/ansible-collections/amazon.aws/pull/171).

Bugfixes
--------

- ec2 - Code fix so module can create ec2 instances with ``ec2_volume_iops`` option (https://github.com/ansible-collections/amazon.aws/pull/177).
- ec2 - ignore terminated instances and instances that are shutting down when starting and stopping (https://github.com/ansible-collections/amazon.aws/issues/146).
- ec2_group - Fixes error handling during tagging failures (https://github.com/ansible-collections/amazon.aws/issues/210).
- ec2_group_info - Code fix so module works with Python 3.8 (make dict immutable in loop) (https://github.com/ansible-collections/amazon.aws/pull/181)

v1.2.1
======

Minor Changes
-------------

- ec2_eni - Add support for tagging.
- ec2_eni - Port ec2_eni module to boto3 and add an integration test suite.
- ec2_eni_info - Add retries on transient AWS failures.
- ec2_eni_info - Add support for providing an ENI ID.

v1.2.0
======

Minor Changes
-------------

- ec2 module_utils - Update ``ec2_connect`` (boto2) behaviour so that ``ec2_url`` overrides ``region``.
- module_utils.core - Support passing arbitrary extra keys to fail_json_aws, matching capabilities of fail_json.

Deprecated Features
-------------------

- All AWS Modules - ``aws_access_key``, ``aws_secret_key`` and ``security_token`` will be made mutually exclusive with ``profile`` after 2022-06-01.

Bugfixes
--------

- ec2 module_utils - Ensure boto3 verify parameter isn't overridden by setting a profile (https://github.com/ansible-collections/amazon.aws/issues/129)
- s3_bucket - Ceph compatibility: treat error code NoSuchTagSetError used by Ceph synonymously to NoSuchTagSet used by AWS

v1.1.0
======

Major Changes
-------------

- ec2 module_utils - The ``AWSRetry`` decorator no longer catches ``NotFound`` exceptions by default.  ``NotFound`` exceptions need to be explicitly added using ``catch_extra_error_codes``.  Some AWS modules may see an increase in transient failures due to AWS''s eventual consistency model.

Minor Changes
-------------

- Add `aws_security_token`, `aws_endpoint_url` and `endpoint_url` aliases to improve AWS module parameter naming consistency.
- Add support for `aws_ca_bundle` to boto3 based AWS modules
- Add support for configuring boto3 profiles using `AWS_PROFILE` and `AWS_DEFAULT_PROFILE`
- Added check_mode support to aws_az_info
- Added check_mode support to ec2_eni_info
- Added check_mode support to ec2_snapshot_info
- ansible_dict_to_boto3_filter_list - convert integers and bools to strings before using them in filters.
- aws_direct_connect_virtual_interface - add direct_connect_gateway_id parameter. This field is only applicable in private VIF cases (public=False) and is mutually exclusive to virtual_gateway_id.
- cloudformation - Return change_set_id in the cloudformation output if a change set was created.
- ec2 - deprecate allowing both group and group_id - currently we ignore group_id if both are passed.
- ec2_ami_info - allow integer and bool values for filtering images (https://github.com/ansible/ansible/issues/43570).
- ec2_asg - Add support for Max Instance Lifetime
- ec2_asg - Add the ability to use mixed_instance_policy in launch template driven autoscaling groups
- ec2_asg - Migrated to AnsibleAWSModule
- ec2_placement_group - make `name` a required field.
- ec2_vol_info - Code cleanup and use of the AWSRetry decorator to improve stability
- ec2_vpc_net - Enable IPv6 CIDR assignment

Breaking Changes / Porting Guide
--------------------------------

- aws_s3 - can now delete versioned buckets even when they are not empty - set mode to delete to delete a versioned bucket and everything in it.

Deprecated Features
-------------------

- cloudformation - The ``template_format`` option had no effect since Ansible 2.3 and will be removed after 2022-06-01
- cloudformation - the ``template_format`` option has been deprecated and will be removed in a later release. It has been ignored by the module since Ansible 2.3.
- data_pipeline - The ``version`` option had no effect and will be removed in after 2022-06-01
- ec2 - in a later release, the ``group`` and ``group_id`` options will become mutually exclusive.  Currently ``group_id`` is ignored if you pass both.
- ec2_ami - The ``no_device`` alias ``NoDevice`` has been deprecated  and will be removed after 2022-06-01
- ec2_ami - The ``virtual_name`` alias ``VirtualName`` has been deprecated and will be removed after 2022-06-01
- ec2_eip - The ``wait_timeout`` option had no effect and will be removed after 2022-06-01
- ec2_key - The ``wait_timeout`` option had no effect and will be removed after 2022-06-01
- ec2_key - The ``wait`` option had no effect and will be removed after 2022-06-01
- ec2_key - the ``wait_timeout`` option has been deprecated and will be removed in a later release. It has had no effect since Ansible 2.5.
- ec2_key - the ``wait`` option has been deprecated and will be removed in a later release. It has had no effect since Ansible 2.5.
- ec2_lc - The ``associate_public_ip_address`` option had no effect and will be removed after 2022-06-01
- ec2_tag - deprecate the ``list`` option in favor of ec2_tag_info
- ec2_tag - support for ``list`` as a state has been deprecated and will be removed in a later release.  The ``ec2_tag_info`` can be used to fetch the tags on an EC2 resource.

Bugfixes
--------

- aws_ec2 - fix idempotency when managing tags
- aws_ec2 - fix idempotency when metrics are enable
- aws_s3 - Delete objects and delete markers so versioned buckets can be removed.
- aws_s3 - Try to wait for the bucket to exist before setting the access control list.
- cloudformation_info - Fix a KeyError returning information about the stack(s).
- ec2_asg - Ensure "wait" is honored during replace operations
- ec2_launch_template - Update output to include latest_version and default_version, matching the documentation
- ec2_transit_gateway - Use AWSRetry before ClientError is handled when describing transit gateways
- ec2_transit_gateway - fixed issue where auto_attach set to yes was not being honored (https://github.com/ansible/ansible/issues/61907)
- ec2_vol - fix filtering bug
- s3_bucket - Accept XNotImplemented response to support NetApp StorageGRID.
