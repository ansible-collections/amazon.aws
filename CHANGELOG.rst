===========================
community.aws Release Notes
===========================

.. contents:: Topics


v4.0.0
======

Major Changes
-------------

- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.20.0`` and ``boto3<1.17.0``. Most modules will continue to work with older versions of the AWS SDK, however compatability with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/574).

Minor Changes
-------------

- aws_s3 - Add ``validate_bucket_name`` option, to control bucket name validation (https://github.com/ansible-collections/amazon.aws/pull/615).
- aws_s3 - The ``aws_s3`` module has been renamed to ``s3_object`` (https://github.com/ansible-collections/amazon.aws/pull/869).
- aws_s3 - ``resource_tags`` has been added as an alias for the ``tags`` parameter (https://github.com/ansible-collections/amazon.aws/pull/845).
- ec2_eni - Change parameter ``device_index`` data type to string when passing to `describe_network_inter` api call (https://github.com/ansible-collections/amazon.aws/pull/877).
- ec2_eni - ``resource_tags`` has been added as an alias for the ``tags`` parameter (https://github.com/ansible-collections/amazon.aws/pull/845).
- ec2_group - add ``egress_rules`` as an alias for ``rules_egress`` (https://github.com/ansible-collections/amazon.aws/pull/878).
- ec2_group - add ``purge_egress_rules`` as an alias for ``purge_rules_egress`` (https://github.com/ansible-collections/amazon.aws/pull/878).
- ec2_instance - Add missing ``metadata_options`` parameters (https://github.com/ansible-collections/amazon.aws/pull/715).
- ec2_key - ``resource_tags`` has been added as an alias for the ``tags`` parameter (https://github.com/ansible-collections/amazon.aws/pull/845).
- ec2_vpc_net - add support for managing VPCs by ID (https://github.com/ansible-collections/amazon.aws/pull/848).
- ec2_vpc_subnet - add support for OutpostArn param (https://github.com/ansible-collections/amazon.aws/pull/598).
- elb_classic_lb - ``resource_tags`` has been added as an alias for the ``tags`` parameter (https://github.com/ansible-collections/amazon.aws/pull/845).
- s3_bucket - Add ``validate_bucket_name`` option, to control bucket name validation (https://github.com/ansible-collections/amazon.aws/pull/615).
- s3_bucket - ``resource_tags`` has been added as an alias for the ``tags`` parameter (https://github.com/ansible-collections/amazon.aws/pull/845).

Breaking Changes / Porting Guide
--------------------------------

- Tags beginning with ``aws:`` will not be removed when purging tags, these tags are reserved by Amazon and may not be updated or deleted (https://github.com/ansible-collections/amazon.aws/issues/817).
- amazon.aws collection - the ``profile`` parameter is now mutually exclusive with the ``aws_access_key``, ``aws_secret_key`` and ``security_token`` parameters (https://github.com/ansible-collections/amazon.aws/pull/834).
- aws_az_info - the module alias ``aws_az_facts`` was deprecated in Ansible 2.9 and has now been removed (https://github.com/ansible-collections/amazon.aws/pull/832).
- aws_s3 - the default value for ``ensure overwrite`` has been changed to ``different`` instead of ``always`` so that the module is idempotent by default (https://github.com/ansible-collections/amazon.aws/issues/811).
- aws_ssm - on_denied and on_missing now both default to error, for consistency with both aws_secret and the base Lookup class (https://github.com/ansible-collections/amazon.aws/issues/617).
- ec2 - The ``ec2`` module has been removed in release 4.0.0 and replaced by the ``ec2_instance`` module (https://github.com/ansible-collections/amazon.aws/pull/630).
- ec2_vpc_igw_info - The default value for ``convert_tags`` has been changed to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/835).
- elb_classic_lb - the ``ec2_elb`` fact has been removed (https://github.com/ansible-collections/amazon.aws/pull/827).
- module_utils - Support for the original AWS SDK aka ``boto`` has been removed, including all relevant helper functions. All modules should now use the ``boto3``/``botocore`` AWS SDK (https://github.com/ansible-collections/amazon.aws/pull/630)

Deprecated Features
-------------------

- aws_s3 - The ``S3_URL`` alias for the s3_url option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- ec2_ami - The ``DeviceName`` alias for the device_name option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- ec2_ami - The ``NoDevice`` alias for the no_device option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- ec2_ami - The ``VirtualName`` alias for the virtual_name option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- ec2_ami - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/846).
- ec2_instance - The default value for ```instance_type``` has been deprecated, in the future release you must set an instance_type or a launch_template (https://github.com/ansible-collections/amazon.aws/pull/587).
- ec2_instance - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/849).
- ec2_key - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/846).
- ec2_vol - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/846).
- ec2_vpc_dhcp_option_info - The ``DhcpOptionIds`` alias for the dhcp_option_ids option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- ec2_vpc_dhcp_option_info - The ``DryRun`` alias for the dry_run option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- ec2_vpc_endpoint - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/846).
- ec2_vpc_net - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/848).
- ec2_vpc_route_table - the current default value of ``False`` for ``purge_tags`` has been deprecated and will be updated in release 5.0.0 to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/846).
- s3_bucket - The ``S3_URL`` alias for the s3_url option has been deprecated and will be removed in release 5.0.0 (https://github.com/ansible-collections/community.aws/pull/795).
- s3_object - Support for creation and deletion of S3 buckets has been deprecated.  Please use the ``amazon.aws.s3_bucket`` module to create and delete buckets (https://github.com/ansible-collections/amazon.aws/pull/869).

Removed Features (previously deprecated)
----------------------------------------

- cloudformation - the ``template_format`` option has been removed. It has been ignored by the module since Ansible 2.3 (https://github.com/ansible-collections/amazon.aws/pull/833).
- ec2_key - the ``wait_timeout`` option had no effect, was deprecated in release 1.0.0, and has now been removed (https://github.com/ansible-collections/amazon.aws/pull/830).
- ec2_key - the ``wait`` option had no effect, was deprecated in release 1.0.0, and has now been removed (https://github.com/ansible-collections/amazon.aws/pull/830).
- ec2_tag - the previously deprecated state ``list`` has been removed.  To list tags on an EC2 resource the ``ec2_tag_info`` module can be used (https://github.com/ansible-collections/amazon.aws/pull/829).
- ec2_vol - the previously deprecated state ``list`` has been removed.  To list volumes the ``ec2_vol_info`` module can be used (https://github.com/ansible-collections/amazon.aws/pull/828).
- module_utils.batch - the class ``ansible_collections.amazon.aws.plugins.module_utils.batch.AWSConnection`` has been removed.  Please use ``AnsibleAWSModule.client()`` instead (https://github.com/ansible-collections/amazon.aws/pull/831).

Bugfixes
--------

- ec2_group - fix uncaught exception when running with ``--diff`` and ``--check`` to create a new security group (https://github.com/ansible-collections/amazon.aws/issues/440).
- ec2_instance - Add a condition to handle default ```instance_type``` value for fix breaking on instance creation with launch template (https://github.com/ansible-collections/amazon.aws/pull/587).
- ec2_instance - raise an error when missing permission to stop instance when ``state`` is set to ``rebooted``` (https://github.com/ansible-collections/amazon.aws/pull/671).
- ec2_vpc_igw - use gateway_id rather than filters to paginate if possible to fix 'NoneType' object is not subscriptable error (https://github.com/ansible-collections/amazon.aws/pull/766).
- ec2_vpc_net - fix a bug where CIDR configuration would be updated in check mode (https://github.com/ansible/ansible/issues/62678).
- ec2_vpc_net - fix a bug where the module would get stuck if DNS options were updated in check mode (https://github.com/ansible/ansible/issues/62677).
- elb_classic_lb - modify the return value of _format_listeners method to resolve a failure creating https listeners (https://github.com/ansible-collections/amazon.aws/pull/860).

v3.3.0
======

Minor Changes
-------------

- aws_ec2 inventory - Allow for literal strings in hostname that don't match filter parameters in ec2 describe-instances (https://github.com/ansible-collections/amazon.aws/pull/826).
- aws_ssm - Add support for ``endpoint`` parameter (https://github.com/ansible-collections/amazon.aws/pull/837).
- module.utils.rds - add retry_codes to get_rds_method_attribute return data to use in call_method and add unit tests (https://github.com/ansible-collections/amazon.aws/pull/776).
- module.utils.rds - refactor to utilize get_rds_method_attribute return data (https://github.com/ansible-collections/amazon.aws/pull/776).
- module_utils - add new aliases ``aws_session_token`` and ``session_token`` to the ``security_token`` parameter to be more in-line with the boto SDK (https://github.com/ansible-collections/amazon.aws/pull/631).
- module_utils.rds - Add support and unit tests for addition/removal of IAM roles to/from a db instance in module_utils.rds with waiters (https://github.com/ansible-collections/amazon.aws/pull/714).

Bugfixes
--------

- Include ``PSF-license.txt`` file for ``plugins/module_utils/_version.py``.
- aws_account_attribute lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_ec2 inventory plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_rds inventory plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_resource_actions callback plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_secret lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_service_ip_ranges lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_ssm - Fix environment variables for client configuration (e.g., AWS_PROFILE, AWS_ACCESS_KEY_ID) (https://github.com/ansible-collections/amazon.aws/pull/837).
- aws_ssm lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- ec2_instance - ec2_instance module broken in Python 3.8 - dict keys modified during iteration (https://github.com/ansible-collections/amazon.aws/issues/709).
- module.utils.rds - Add waiter for promoting read replica to fix idempotency issue (https://github.com/ansible-collections/amazon.aws/pull/714).
- module.utils.rds - Catch InvalidDBSecurityGroupStateFault when modifying a db instance (https://github.com/ansible-collections/amazon.aws/pull/776).
- module.utils.s3 - Update validate_bucket_name minimum length to 3 (https://github.com/ansible-collections/amazon.aws/pull/802).

v3.2.0
======

Minor Changes
-------------

- aws_secret - add pagination for ``bypath`` functionality (https://github.com/ansible-collections/amazon.aws/pull/591).
- ec2_instance - Fix scope of deprecation warning to not show warning when ``state`` in ``absent`` (https://github.com/ansible-collections/amazon.aws/pull/719).
- ec2_vpc_route_table - support associating internet gateways (https://github.com/ansible-collections/amazon.aws/pull/690).
- module_utils.elbv2 - Add support for alb specific attributes and compare_elb_attributes method to support check_mode in module_utils.elbv2 (https://github.com/ansible-collections/amazon.aws/pull/696).
- s3_bucket - Add support for enforced bucket owner object ownership (https://github.com/ansible-collections/amazon.aws/pull/694).

Bugfixes
--------

- aws_ec2 inventory - use the iam_role_arn configuration parameter to assume the role before trying to call DescribeRegions if the regions configuration is not set and AWS credentials provided without enough privilege to perform the DescribeRegions action. (https://github.com/ansible-collections/amazon.aws/issues/566).
- ec2_vol - changing a volume from a type that does not support IOPS (like ``standard``) to a type that does (like ``gp3``) fails (https://github.com/ansible-collections/amazon.aws/issues/626).
- ec2_vpc_igw - fix 'NoneType' object is not subscriptable error (https://github.com/ansible-collections/amazon.aws/pull/691).
- ec2_vpc_igw - use paginator for describe internet gateways and add retry to fix NoneType object is not subscriptable error (https://github.com/ansible-collections/amazon.aws/pull/695).
- ec2_vpc_net - In check mode, ensure the module does not change the configuration. Handle case when Amazon-provided ipv6 block is enabled, then disabled, then enabled again. Do not disable IPv6 CIDR association (using Amazon pool) if ipv6_cidr property is not present in the task. If the VPC already exists and ipv6_cidr property, retain the current config (https://github.com/ansible-collections/amazon.aws/pull/631).

v3.1.1
======

Minor Changes
-------------

- bump the release version of the amazon.aws collection from 3.1.0 to 3.1.1 because of a bug that occurred while uploading to Galaxy.

v3.1.0
======

Minor Changes
-------------

- add new parameters hostvars_prefix and hostvars_suffix for inventory plugins aws_ec2 and aws_rds (https://github.com/ansible-collections/amazon.aws/issues/535).
- aws_s3 - Add ``validate_bucket_name`` option, to control bucket name validation (https://github.com/ansible-collections/amazon.aws/pull/615).
- aws_s3 - add latest choice on ``overwrite`` parameter to get latest object on S3 (https://github.com/ansible-collections/amazon.aws/pull/595).
- ec2_vol - add support for OutpostArn param (https://github.com/ansible-collections/amazon.aws/pull/597).
- ec2_vol - tag volume on creation (https://github.com/ansible-collections/amazon.aws/pull/603).
- ec2_vpc_route_table - add support for IPv6 in creating route tables (https://github.com/ansible-collections/amazon.aws/pull/601).
- s3_bucket - Add ``validate_bucket_name`` option, to control bucket name validation (https://github.com/ansible-collections/amazon.aws/pull/615).

Deprecated Features
-------------------

- ec2_instance - The default value for ```instance_type``` has been deprecated, in the future release you must set an instance_type or a launch_template (https://github.com/ansible-collections/amazon.aws/pull/587).

Bugfixes
--------

- Various modules and plugins - use vendored version of ``distutils.version`` instead of the deprecated Python standard library ``distutils`` (https://github.com/ansible-collections/amazon.aws/pull/599).
- aws_acm - No longer raising ResourceNotFound exception while retrieving ACM certificates.
- aws_s3 - fix exception raised when using module to copy from source to destination and key is missing from source (https://github.com/ansible-collections/amazon.aws/issues/602).
- ec2_instance - Add a condition to handle default ```instance_type``` value for fix breaking on instance creation with launch template (https://github.com/ansible-collections/amazon.aws/pull/587).
- ec2_key - add support for ED25519 key type (https://github.com/ansible-collections/amazon.aws/issues/572).
- ec2_vol - Sets the Iops value in req_obj even if the iops value has not changed, to allow modifying volume types that require passing an iops value to boto. (https://github.com/ansible-collections/amazon.aws/pull/606)
- elb_classic_lb - handle security_group_ids when providing security_group_names and fix broken tasks in integration test (https://github.com/ansible-collections/amazon.aws/pull/592).
- s3_bucket - Enable the management of bucket-level ACLs (https://github.com/ansible-collections/amazon.aws/issues/573).

v3.0.0
======

Major Changes
-------------

- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.19.0`` and ``boto3<1.16.0``. Most modules will continue to work with older versions of the AWS SDK, however compatability with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/574).

Minor Changes
-------------

- ec2_instance - add count parameter support (https://github.com/ansible-collections/amazon.aws/pull/539).

Breaking Changes / Porting Guide
--------------------------------

- aws_caller_facts - Remove deprecated ``aws_caller_facts`` alias.  Please use ``aws_caller_info`` instead.
- cloudformation_facts - Remove deprecated ``cloudformation_facts`` alias.  Please use ``cloudformation_info`` instead.
- ec2_ami_facts - Remove deprecated ``ec2_ami_facts`` alias.  Please use ``ec2_ami_info`` instead.
- ec2_eni_facts - Remove deprecated ``ec2_eni_facts`` alias.  Please use ``ec2_eni_info`` instead.
- ec2_group_facts - Remove deprecated ``ec2_group_facts`` alias.  Please use ``ec2_group_info`` instead.
- ec2_instance_facts - Remove deprecated ``ec2_instance_facts`` alias.  Please use ``ec2_instance_info`` instead.
- ec2_snapshot_facts - Remove deprecated ``ec2_snapshot_facts`` alias.  Please use ``ec2_snapshot_info`` instead.
- ec2_vol_facts - Remove deprecated ``ec2_vol_facts`` alias.  Please use ``ec2_vol_info`` instead.
- ec2_vpc_dhcp_option_facts - Remove deprecated ``ec2_vpc_dhcp_option_facts`` alias.  Please use ``ec2_vpc_dhcp_option_info`` instead.
- ec2_vpc_endpoint_facts - Remove deprecated ``ec2_vpc_endpoint_facts`` alias.  Please use ``ec2_vpc_endpoint_info`` instead.
- ec2_vpc_igw_facts - Remove deprecated ``ec2_vpc_igw_facts`` alias.  Please use ``ec2_vpc_igw_info`` instead.
- ec2_vpc_nat_gateway_facts - Remove deprecated ``ec2_vpc_nat_gateway_facts`` alias.  Please use ``ec2_vpc_nat_gateway_info`` instead.
- ec2_vpc_net_facts - Remove deprecated ``ec2_vpc_net_facts`` alias.  Please use ``ec2_vpc_net_info`` instead.
- ec2_vpc_route_table_facts - Remove deprecated ``ec2_vpc_route_table_facts`` alias.  Please use ``ec2_vpc_route_table_info`` instead.
- ec2_vpc_subnet_facts - Remove deprecated ``ec2_vpc_subnet_facts`` alias.  Please use ``ec2_vpc_subnet_info`` instead.

Deprecated Features
-------------------

- module_utils - support for the original AWS SDK `boto` has been deprecated in favour of the `boto3`/`botocore` SDK. All `boto` based modules have either been deprecated or migrated to `botocore`, and the remaining support code in module_utils will be removed in release 4.0.0 of the amazon.aws collection. Any modules outside of the amazon.aws and community.aws collections based on the `boto` library will need to be migrated to the `boto3`/`botocore` libraries (https://github.com/ansible-collections/amazon.aws/pull/575).

v2.2.0
======

Minor Changes
-------------

- ec2_instance - add count parameter support (https://github.com/ansible-collections/amazon.aws/pull/539).

Bugfixes
--------

- aws_ec2 inventory - use the iam_role_arn configuration parameter to assume the role before trying to call DescribeRegions if the regions configuration is not set and AWS credentials provided without enough privilege to perform the DescribeRegions action. (https://github.com/ansible-collections/amazon.aws/issues/566).
- ec2_vol - Sets the Iops value in req_obj even if the iops value has not changed, to allow modifying volume types that require passing an iops value to boto. (https://github.com/ansible-collections/amazon.aws/pull/606)
- ec2_vol - changing a volume from a type that does not support IOPS (like ``standard``) to a type that does (like ``gp3``) fails (https://github.com/ansible-collections/amazon.aws/issues/626).
- ec2_vpc_igw - fix 'NoneType' object is not subscriptable error (https://github.com/ansible-collections/amazon.aws/pull/691).
- ec2_vpc_igw - use paginator for describe internet gateways and add retry to fix NoneType object is not subscriptable error (https://github.com/ansible-collections/amazon.aws/pull/695).
- elb_classic_lb - handle security_group_ids when providing security_group_names and fix broken tasks in integration test (https://github.com/ansible-collections/amazon.aws/pull/592).

v2.1.0
======

Minor Changes
-------------

- aws_service_ip_ranges - add new option ``ipv6_prefixes`` to get only IPV6 addresses and prefixes for Amazon services (https://github.com/ansible-collections/amazon.aws/pull/430)
- cloudformation - fix detection when there are no changes. Sometimes when there are no changes, the change set will have a status FAILED with StatusReason No updates are to be performed (https://github.com/ansible-collections/amazon.aws/pull/507).
- ec2_ami - add check_mode support (https://github.com/ansible-collections/amazon.aws/pull/516).
- ec2_ami - use module_util helper for tagging AMIs (https://github.com/ansible-collections/amazon.aws/pull/520).
- ec2_ami - when creating an AMI from an instance pass the tagging options at creation time (https://github.com/ansible-collections/amazon.aws/pull/551).
- ec2_elb_lb - module renamed to ``elb_classic_lb`` (https://github.com/ansible-collections/amazon.aws/pull/377).
- ec2_eni - add check mode support (https://github.com/ansible-collections/amazon.aws/pull/534).
- ec2_eni - use module_util helper for tagging ENIs (https://github.com/ansible-collections/amazon.aws/pull/522).
- ec2_instance - use module_util helpers for tagging (https://github.com/ansible-collections/amazon.aws/pull/527).
- ec2_key - add support for tagging key pairs (https://github.com/ansible-collections/amazon.aws/pull/548).
- ec2_snapshot - add check_mode support (https://github.com/ansible-collections/amazon.aws/pull/512).
- ec2_vol - add check_mode support (https://github.com/ansible-collections/amazon.aws/pull/509).
- ec2_vpc_dhcp_option - use module_util helpers for tagging (https://github.com/ansible-collections/amazon.aws/pull/531).
- ec2_vpc_endpoint - added ``vpc_endpoint_security_groups`` parameter to support defining the security group attached to an interface endpoint (https://github.com/ansible-collections/amazon.aws/pull/544).
- ec2_vpc_endpoint - added ``vpc_endpoint_subnets`` parameter to support defining the subnet attached to an interface or gateway endpoint (https://github.com/ansible-collections/amazon.aws/pull/544).
- ec2_vpc_endpoint - use module_util helper for tagging (https://github.com/ansible-collections/amazon.aws/pull/525).
- ec2_vpc_endpoint - use module_util helpers for tagging (https://github.com/ansible-collections/amazon.aws/pull/531).
- ec2_vpc_igw - use module_util helper for tagging (https://github.com/ansible-collections/amazon.aws/pull/523).
- ec2_vpc_igw - use module_util helpers for tagging (https://github.com/ansible-collections/amazon.aws/pull/531).
- ec2_vpc_nat_gateway - use module_util helper for tagging (https://github.com/ansible-collections/amazon.aws/pull/524).
- ec2_vpc_nat_gateway - use module_util helpers for tagging (https://github.com/ansible-collections/amazon.aws/pull/531).
- elb_classic_lb - added retries on common AWS temporary API failures (https://github.com/ansible-collections/amazon.aws/pull/377).
- elb_classic_lb - added support for check_mode (https://github.com/ansible-collections/amazon.aws/pull/377).
- elb_classic_lb - added support for wait during creation (https://github.com/ansible-collections/amazon.aws/pull/377).
- elb_classic_lb - added support for wait during instance addition and removal (https://github.com/ansible-collections/amazon.aws/pull/377).
- elb_classic_lb - migrated to boto3 SDK (https://github.com/ansible-collections/amazon.aws/pull/377).
- elb_classic_lb - various error messages changed due to refactor (https://github.com/ansible-collections/amazon.aws/pull/377).
- module_utils.ec2 - moved generic tagging helpers into module_utils.tagging (https://github.com/ansible-collections/amazon.aws/pull/527).
- module_utils.tagging - add new helper to generate TagSpecification lists (https://github.com/ansible-collections/amazon.aws/pull/527).

Deprecated Features
-------------------

- ec2_classic_lb - setting of the ``ec2_elb`` fact has been deprecated and will be removed in release 4.0.0 of the collection. The module now returns ``elb`` which can be accessed using the register keyword (https://github.com/ansible-collections/amazon.aws/pull/552).

Bugfixes
--------

- AWS action group - added missing ``ec2_instance_facts`` entry (https://github.com/ansible-collections/amazon.aws/issues/557)
- ec2_ami - fix problem when creating an AMI from an instance with ephemeral volumes (https://github.com/ansible-collections/amazon.aws/issues/511).
- ec2_instance - ensure that ec2_instance falls back to the tag(Name) parameter when no filter and no name parameter is passed (https://github.com/ansible-collections/amazon.aws/issues/526).
- s3_bucket - update error handling to better support DigitalOcean Space (https://github.com/ansible-collections/amazon.aws/issues/508).

v2.0.0
======

Major Changes
-------------

- amazon.aws collection - Due to the AWS SDKs announcing the end of support for Python less than 3.6 (https://boto3.amazonaws.com/v1/documentation/api/1.17.64/guide/migrationpy3.html) this collection now requires Python 3.6+ (https://github.com/ansible-collections/amazon.aws/pull/298).
- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.18.0`` and ``boto3<1.15.0``. Most modules will continue to work with older versions of the AWS SDK, however compatability with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/502).
- ec2_instance - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_instance``.
- ec2_instance_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_instance_info``.
- ec2_vpc_endpoint - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_endpoint``.
- ec2_vpc_endpoint_facts - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_endpoint_info``.
- ec2_vpc_endpoint_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_endpoint_info``.
- ec2_vpc_endpoint_service_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_endpoint_service_info``.
- ec2_vpc_igw - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_igw``.
- ec2_vpc_igw_facts - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_igw_facts``.
- ec2_vpc_igw_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_igw_info``.
- ec2_vpc_nat_gateway - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_nat_gateway``.
- ec2_vpc_nat_gateway_facts - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_nat_gateway_info``.
- ec2_vpc_nat_gateway_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_nat_gateway_info``.
- ec2_vpc_route_table - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_route_table``.
- ec2_vpc_route_table_facts - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_route_table_facts``.
- ec2_vpc_route_table_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_route_table_info``.

Minor Changes
-------------

- aws_ec2 - use a generator rather than list comprehension (https://github.com/ansible-collections/amazon.aws/pull/465).
- aws_s3 - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- aws_s3 - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- aws_s3 - add ``tags`` and ``purge_tags`` features for an S3 object (https://github.com/ansible-collections/amazon.aws/pull/335)
- aws_s3 - new mode to copy existing on another bucket (https://github.com/ansible-collections/amazon.aws/pull/359).
- aws_secret - added support for gracefully handling deleted secrets (https://github.com/ansible-collections/amazon.aws/pull/455).
- aws_ssm - add "on_missing" and "on_denied" option (https://github.com/ansible-collections/amazon.aws/pull/370).
- cloudformation - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- cloudformation - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_ami - ensure tags are propagated to the snapshot(s) when creating an AMI (https://github.com/ansible-collections/amazon.aws/pull/437).
- ec2_eni - fix idempotency when ``security_groups`` attribute is specified (https://github.com/ansible-collections/amazon.aws/pull/337).
- ec2_eni - timeout increased when waiting for ENIs to finish detaching (https://github.com/ansible-collections/amazon.aws/pull/501).
- ec2_group - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_group - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_group - use a generator rather than list comprehension (https://github.com/ansible-collections/amazon.aws/pull/465).
- ec2_group - use system ipaddress module, available with Python >= 3.3, instead of vendored copy (https://github.com/ansible-collections/amazon.aws/pull/461).
- ec2_instance - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_instance - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_instance - add ``throughput`` parameter for gp3 volume types (https://github.com/ansible-collections/amazon.aws/pull/433).
- ec2_instance - add support for controlling metadata options (https://github.com/ansible-collections/amazon.aws/pull/414).
- ec2_instance - remove unnecessary raise when exiting with a failure (https://github.com/ansible-collections/amazon.aws/pull/460).
- ec2_instance_info - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_instance_info - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_snapshot - migrated to use the boto3 python library (https://github.com/ansible-collections/amazon.aws/pull/356).
- ec2_spot_instance_info - Added a new module that describes the specified Spot Instance requests (https://github.com/ansible-collections/amazon.aws/pull/487).
- ec2_vol - add parameter ``multi_attach`` to support Multi-Attach on volume creation/update (https://github.com/ansible-collections/amazon.aws/pull/362).
- ec2_vol - relax the boto3/botocore requirements and only require botocore 1.19.27 for modifying the ``throughput`` parameter (https://github.com/ansible-collections/amazon.aws/pull/346).
- ec2_vpc_dhcp_option - Now also returns a boto3-style resource description in the ``dhcp_options`` result key.  This includes any tags for the ``dhcp_options_id`` and has the same format as the current return value of ``ec2_vpc_dhcp_option_info``. (https://github.com/ansible-collections/amazon.aws/pull/252)
- ec2_vpc_dhcp_option_info - Now also returns a user-friendly ``dhcp_config`` key that matches the historical ``new_config`` key from ec2_vpc_dhcp_option, and alleviates the need to use ``items2dict(key_name='key', value_name='values')`` when parsing the output of the module. (https://github.com/ansible-collections/amazon.aws/pull/252)
- ec2_vpc_subnet - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_vpc_subnet - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- integration tests - remove dependency with collection ``community.general`` (https://github.com/ansible-collections/amazon.aws/pull/361).
- module_utils/waiter - add RDS cluster ``cluster_available`` waiter (https://github.com/ansible-collections/amazon.aws/pull/464).
- module_utils/waiter - add RDS cluster ``cluster_deleted`` waiter (https://github.com/ansible-collections/amazon.aws/pull/464).
- module_utils/waiter - add Route53 ``resource_record_sets_changed`` waiter (https://github.com/ansible-collections/amazon.aws/pull/350).
- s3_bucket - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- s3_bucket - Tests for compatability with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- s3_bucket - add new option ``object_ownership`` to configure object ownership (https://github.com/ansible-collections/amazon.aws/pull/311)
- s3_bucket - updated to use HeadBucket instead of ListBucket when testing for bucket existence (https://github.com/ansible-collections/amazon.aws/pull/357).

Breaking Changes / Porting Guide
--------------------------------

- ec2_instance - instance wait for state behaviour has changed.  If plays require the old behavior of waiting for the instance monitoring status to become ``OK`` when launching a new instance, the action will need to specify ``state: started`` (https://github.com/ansible-collections/amazon.aws/pull/481).
- ec2_snapshot - support for waiting indefinitely has been dropped, new default is 10 minutes (https://github.com/ansible-collections/amazon.aws/pull/356).
- ec2_vol_info - return ``attachment_set`` is now a list of attachments with Multi-Attach support on disk. (https://github.com/ansible-collections/amazon.aws/pull/362).
- ec2_vpc_dhcp_option - The module has been refactored to use boto3. Keys and value types returned by the module are now consistent, which is a change from the previous behaviour. A ``purge_tags`` option has been added, which defaults to ``True``.  (https://github.com/ansible-collections/amazon.aws/pull/252)
- ec2_vpc_dhcp_option_info - Now preserves case for tag keys in return value. (https://github.com/ansible-collections/amazon.aws/pull/252)
- module_utils.core - The boto3 switch has been removed from the region parameter (https://github.com/ansible-collections/amazon.aws/pull/287).
- module_utils/compat - vendored copy of ipaddress removed (https://github.com/ansible-collections/amazon.aws/pull/461).
- module_utils/core - updated the ``scrub_none_parameters`` function so that ``descend_into_lists`` is set to ``True`` by default (https://github.com/ansible-collections/amazon.aws/pull/297).

Deprecated Features
-------------------

- ec2 - the boto based ``ec2`` module has been deprecated in favour of the boto3 based ``ec2_instance`` module. The ``ec2`` module will be removed in release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/424).
- ec2_vpc_dhcp_option - The ``new_config`` return key has been deprecated and will be removed in a future release.  It will be replaced by ``dhcp_config``.  Both values are returned in the interim. (https://github.com/ansible-collections/amazon.aws/pull/252)

Bugfixes
--------

- aws_s3 - Fix upload permission when an S3 bucket ACL policy requires a particular canned ACL (https://github.com/ansible-collections/amazon.aws/pull/318)
- ec2_ami - Fix ami issue when creating an ami with no_device parameter (https://github.com/ansible-collections/amazon.aws/pull/386)
- ec2_instance - ``ec2_instance`` was waiting on EC2 instance monitoring status to be ``OK`` when launching a new instance. This could cause a play to wait multiple minutes for AWS's monitoring to complete status checks (https://github.com/ansible-collections/amazon.aws/pull/481).
- ec2_snapshot - Fix snapshot issue when capturing a snapshot of a volume without tags (https://github.com/ansible-collections/amazon.aws/pull/383)
- ec2_vol - Fixes ``changed`` status when ``modify_volume`` is used, but no new  disk is being attached.  The module incorrectly reported that no change had  occurred even when disks had been modified (iops, throughput, type, etc.). (https://github.com/ansible-collections/amazon.aws/issues/482).
- ec2_vol - fix iops setting and enforce iops/throughput parameters usage (https://github.com/ansible-collections/amazon.aws/pull/334)
- inventory - ``include_filters`` won't be ignored anymore if ``filters`` is not set (https://github.com/ansible-collections/amazon.aws/issues/457).
- s3_bucket - Fix error handling when attempting to set a feature that is not implemented (https://github.com/ansible-collections/amazon.aws/pull/391).
- s3_bucket - Gracefully handle ``NotImplemented`` exceptions when fetching encryption settings (https://github.com/ansible-collections/amazon.aws/issues/390).

New Modules
-----------

- ec2_spot_instance - request, stop, reboot or cancel spot instance
- ec2_spot_instance_info - Gather information about ec2 spot instance requests

v1.5.0
======

Minor Changes
-------------

- AWS inventory plugins - use shared HAS_BOTO3 helper rather than copying code (https://github.com/ansible-collections/amazon.aws/pull/288).
- AWS lookup plugins - use shared HAS_BOTO3 helper rather than copying code (https://github.com/ansible-collections/amazon.aws/pull/288).
- aws_account_attribute - add retries on common AWS failures (https://github.com/ansible-collections/amazon.aws/pull/295).
- aws_ec2 inventory - expose a new configuration key ``use_contrib_script_compatible_ec2_tag_keys`` to reproduce a behavior of the old ``ec2.py`` inventory script. With this option enabled, each tag is exposed using a ``ec2_tag_TAGNAME`` key (https://github.com/ansible-collections/amazon.aws/pull/331).
- aws_ec2 inventory - expose to new keys called ``include_filters`` and ``exclude_filters`` to give the user the ability to compose an inventory with multiple queries (https://github.com/ansible-collections/amazon.aws/pull/328).
- aws_ec2 inventory plugin - Added support for using Jinja2 templates in the authentication fields (https://github.com/ansible-collections/amazon.aws/pull/57).
- cloudformation - added support for StackPolicyDuringUpdateBody (https://github.com/ansible-collections/amazon.aws/pull/155).
- ec2_metadata_facts - add support for IMDSv2 (https://github.com/ansible-collections/amazon.aws/pull/43).
- ec2_snapshot_info - add the ``max_results`` along with ``next_token_id`` option (https://github.com/ansible-collections/amazon.aws/pull/321).
- ec2_tag - use common code for tagging resources (https://github.com/ansible-collections/amazon.aws/pull/309).
- ec2_tag_info - use common code for tagging resources (https://github.com/ansible-collections/amazon.aws/pull/309).
- ec2_vol - add the ``purge_tags`` option (https://github.com/ansible-collections/amazon.aws/pull/242).
- ec2_vol - use common code for tagging resources (https://github.com/ansible-collections/amazon.aws/pull/309).
- ec2_vpc_net - use a custom waiter which can handle API rate limiting (https://github.com/ansible-collections/amazon.aws/pull/270).
- ec2_vpc_subnet - use AWSRetry decorator to more consistently handle API rate limiting (https://github.com/ansible-collections/amazon.aws/pull/270).
- ec2_vpc_subnet - use common code for tagging resources (https://github.com/ansible-collections/amazon.aws/pull/309).
- module_utils.cloudfront_facts - linting cleanup (https://github.com/ansible-collections/amazon.aws/pull/291).
- module_utils.ec2 - linting cleanup (https://github.com/ansible-collections/amazon.aws/pull/291).
- module_utils/core - add a helper function ``normalize_boto3_result`` (https://github.com/ansible-collections/amazon.aws/pull/271).
- module_utils/core - add parameter ``descend_into_lists`` to ``scrub_none_parameters`` helper function (https://github.com/ansible-collections/amazon.aws/pull/262).
- module_utils/ec2 - added additional helper functions for tagging EC2 resources (https://github.com/ansible-collections/amazon.aws/pull/309).
- sanity tests - add ignore.txt for 2.12 (https://github.com/ansible-collections/amazon.aws/pull/315).

Bugfixes
--------

- ec2_vol - create or update now preserves the existing tags, including Name (https://github.com/ansible-collections/amazon.aws/issues/229)
- ec2_vol - fix exception when platform information isn't available (https://github.com/ansible-collections/amazon.aws/issues/305).

v1.4.1
======

Minor Changes
-------------

- module_utils - the ipaddress module utility has been vendored into this collection.  This eliminates the collection dependency on ansible.netcommon (which had removed the library in its 2.0 release).  The ipaddress library is provided for internal use in this collection only. (https://github.com/ansible-collections/amazon.aws/issues/273)-

v1.4.0
======

Minor Changes
-------------

- aws_ec2 - Add hostname options concatenation
- aws_ec2 inventory plugin - avoid a superfluous import of ``ansible.utils.display.Display`` (https://github.com/ansible-collections/amazon.aws/pull/226).
- aws_ec2 module - Replace inverse aws instance-state-name filters !terminated, !shutting-down in favor of postive filters pending, running, stopping, stopped. Issue 235. (https://github.com/ansible-collections/amazon.aws/pull/237)
- aws_secret - add ``bypath`` functionality (https://github.com/ansible-collections/amazon.aws/pull/192).
- ec2_key - add AWSRetry decorator to automatically retry on common temporary failures (https://github.com/ansible-collections/amazon.aws/pull/213).
- ec2_vol - Add support for gp3 volumes and support for modifying existing volumes (https://github.com/ansible-collections/amazon.aws/issues/55).
- module_utils/elbv2 - add logic to compare_rules to suit Values list nested within dicts unique to each field type. Fixes issue (https://github.com/ansible-collections/amazon.aws/issues/187)
- various AWS plugins and module_utils - Cleanup unused imports (https://github.com/ansible-collections/amazon.aws/pull/217).

Bugfixes
--------

- ec2_vol - a creation or update now returns a structure with an up to date list of tags (https://github.com/ansible-collections/amazon.aws/pull/241).

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
