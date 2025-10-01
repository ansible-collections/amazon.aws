========================
amazon.aws Release Notes
========================

.. contents:: Topics

v10.1.2
=======

Release Summary
---------------

This release includes multiple bug fixes.

Bugfixes
--------

- Remove ``ansible.module_utils.six`` imports to avoid warnings (https://github.com/ansible-collections/amazon.aws/pull/2727).
- amazon.aws.autoscaling_instance - setting the state to ``terminated`` had no effect. The fix implements missing instance termination state (https://github.com/ansible-collections/amazon.aws/issues/2719).
- ec2_vpc_nacl - Fix issue when trying to update existing Network ACL rule (https://github.com/ansible-collections/amazon.aws/issues/2592).
- s3_object - Honor headers for content and content_base64 uploads by promoting supported keys (e.g. ContentType, ContentDisposition, CacheControl) to top-level S3 arguments and placing remaining keys under Metadata. This makes content uploads consistent with src uploads. (https://github.com/ansible-collections/amazon.aws)

v10.1.1
=======

Release Summary
---------------

This release includes a bugfix and a documentation update.

Bugfixes
--------

- ec2_instance - corrected typo for InsufficientInstanceCapacity. Fix now will retry Ec2 creation when InsufficientInstanceCapacity error occurs (https://github.com/ansible-collections/amazon.aws/issues/1038).

v10.1.0
=======

Release Summary
---------------

This minor release adds support for ``Route53`` as a hostname.

Minor Changes
-------------

- inventory/aws_ec2 - Adding support for ``Route53`` as hostname (https://github.com/ansible-collections/amazon.aws/pull/2580).

v10.0.0
=======

Release Summary
---------------

This major release introduces new support with the ``aws_ssm`` connection plugin, which has been promoted from ``community.aws``, several bugfixes, minor changes and deprecated features.
Additionally, this release increases the minimum required versions of ``boto3`` and ``botocore`` to 1.34.0 to align with updated AWS SDK support and support for ansible-core < 2.17 has been dropped.
Due to the AWS SDKs announcing the end of support for Python less than 3.8 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/), support for Python less than 3.8 by this collection was deprecated in 9.0.0 release and is removed in this 10.0.0 release.

Major Changes
-------------

- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.34.0`` and ``boto3<1.34.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/2426).
- amazon.aws collection - due to the AWS SDKs announcing the end of support for Python less than 3.8 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/), support for Python less than 3.8 by this collection was deprecated in release 6.0.0 and removed in release 10.0.0. (https://github.com/ansible-collections/amazon.aws/pull/2426).
- connection/aws_ssm - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.aws_ssm``.

Minor Changes
-------------

- module_utils.s3 - added "501" to the list of error codes thrown by S3 replacements (https://github.com/ansible-collections/amazon.aws/issues/2447).
- module_utils/s3 - add initial ErrorHandler for S3 modules (https://github.com/ansible-collections/amazon.aws/pull/2060).
- s3_bucket - migrated to use updated error handlers for better handling of non-AWS errors (https://github.com/ansible-collections/amazon.aws/pull/2478).

Breaking Changes / Porting Guide
--------------------------------

- amazon.aws collection - Support for ansible-core < 2.17 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/2601).
- amazon.aws collection - Support for the ``EC2_ACCESS_KEY`` environment variable was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``access_key`` parameter or ``AWS_ACCESS_KEY_ID`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - Support for the ``EC2_REGION`` environment variable was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``region`` parameter or ``AWS_REGION`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - Support for the ``EC2_SECRET_KEY`` environment variable was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``secret_key`` parameter or ``AWS_SECRET_ACCESS_KEY`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - Support for the ``EC2_SECURITY_TOKEN`` and ``AWS_SECURITY_TOKEN`` environment variables were deprecated in release ``6.0.0`` and have now been removed.  Please use the ``session_token`` parameter or ``AWS_SESSION_TOKEN`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - Support for the ``EC2_URL`` and ``S3_URL`` environment variables were deprecated in release ``6.0.0`` and have now been removed.  Please use the ``endpoint_url`` parameter or ``AWS_URL`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - The ``access_token``, ``aws_security_token`` and ``security_token`` aliases for the ``session_token`` parameter were deprecated in release ``6.0.0`` and have now been removed.  Please use the ``session_token`` name instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - The ``boto_profile`` alias for the ``profile`` parameter was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``profile`` name instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - The ``ec2_access_key`` alias for the ``access_key`` parameter was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``access_key`` name instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - The ``ec2_region`` alias for the ``region`` parameter was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``region`` name instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - The ``ec2_secret_key`` alias for the ``secret_key`` parameter was deprecated in release ``6.0.0`` and has now been removed.  Please use the ``secret_key`` name instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- amazon.aws collection - The ``endpoint``, ``ec2_url`` and ``s3_url`` aliases for the ``endpoint_url`` parameter were deprecated in release ``6.0.0`` and have now been removed.  Please use the ``region`` name instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- docs_fragments - The previously deprecated ``amazon.aws.aws_credentials`` docs fragment has been removed please use ``amazon.aws.common.plugins`` instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- docs_fragments - The previously deprecated ``amazon.aws.aws_region`` docs fragment has been removed please use ``amazon.aws.region.plugins`` instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- docs_fragments - The previously deprecated ``amazon.aws.aws`` docs fragment has been removed please use ``amazon.aws.common.modules`` instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- docs_fragments - The previously deprecated ``amazon.aws.ec2`` docs fragment has been removed please use ``amazon.aws.region.modules`` instead (https://github.com/ansible-collections/amazon.aws/pull/2527).
- ec2_vpc_peering_info - the ``result`` key has been removed from the return value. ``vpc_peering_connections`` should be used instead (https://github.com/ansible-collections/amazon.aws/pull/2618).
- module_utils.botocore - drop deprecated ``boto3`` parameter for ``get_aws_region()`` and ``get_aws_connection_info()``, this parameter has had no effect since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2443).
- module_utils.ec2 - drop deprecated ``boto3`` parameter for ``get_ec2_security_group_ids_from_names()`` and ``get_aws_connection_info()``, this parameter has had no effect since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2603).
- rds_param_group - the redirect has been removed and playbooks should be updated to use rds_instance_param_group (https://github.com/ansible-collections/amazon.aws/pull/2618).

Bugfixes
--------

- s3_bucket - bucket ACLs now consistently returned (https://github.com/ansible-collections/amazon.aws/pull/2478).
- s3_bucket - fixed idempotency when setting bucket ACLs (https://github.com/ansible-collections/amazon.aws/pull/2478).

v9.5.1
======

Release Summary
---------------

This release includes a bugfix and a documentation update.

Bugfixes
--------

- ec2_instance - corrected typo for InsufficientInstanceCapacity. Fix now will retry Ec2 creation when InsufficientInstanceCapacity error occurs (https://github.com/ansible-collections/amazon.aws/issues/1038).

v9.5.0
======

Release Summary
---------------

This minor release includes several bugfixes and new features for the ``route53_info`` and ``iam_user_info`` modules.

Minor Changes
-------------

- Bump version of ansible-lint to 25.1.2 (https://github.com/ansible-collections/amazon.aws/pull/2590).
- iam_user_info - Add tags to ListUsers or GetGroup results (https://github.com/ansible-collections/amazon.aws/pull/2567).
- iam_user_info - Return empty user list when invalid group name is provided instead of python error (https://github.com/ansible-collections/amazon.aws/pull/2567).
- module_utils/modules.py - call to ``deprecate()`` without specifying ``collection_name``, ``version`` or ``date`` arguments raises a sanity errors (https://github.com/ansible-collections/amazon.aws/pull/2607).

Bugfixes
--------

- iam_user_info - Actually call GetUser when only user name is supplied instead of listing and filtering from all users (https://github.com/ansible-collections/amazon.aws/pull/2567).
- iam_user_info - Actually filter users by path prefix when one is provided (https://github.com/ansible-collections/amazon.aws/pull/2567).
- route53_info - removes jijna delimiters from example using when (https://github.com/ansible-collections/amazon.aws/issues/2594).

v9.4.0
======

Release Summary
---------------

This minor release includes bug fixes and minor changes to validate the collection against the future ``ansible-core 2.19`` version.

Minor Changes
-------------

- inventory/aws_ec2 - Update templating mechanism to support ansible-core 2.19 changes (https://github.com/ansible-collections/amazon.aws/pull/2552).

Bugfixes
--------

- lookup/aws_account_attribute - plugin should return a list when ``wantlist=True`` (https://github.com/ansible-collections/amazon.aws/pull/2552).

v9.3.0
======

Release Summary
---------------

This minor release includes two new modules (``ec2_dedicated_host`` and ``ec2_dedicated_host_info``) and a new feature for the ``s3_object`` module that now supports passing metadata in ``create`` mode.

Minor Changes
-------------

- s3_object - support passing metadata in ``create`` mode (https://github.com/ansible-collections/amazon.aws/pull/2529).

New Modules
-----------

- ec2_dedicated_host - Create, update or delete (release) EC2 dedicated host
- ec2_dedicated_host_info - Gather information about EC2 Dedicated Hosts in AWS

v9.2.0
======

Release Summary
---------------

This release includes a new module ``route53_key_signing_key``, bug fixes, minor changes, and linting corrections across multiple modules.

Minor Changes
-------------

- autoscaling_group - avoid assignment to unused variable in except block (https://github.com/ansible-collections/amazon.aws/pull/2464).
- ec2_ami - avoid redefining ``delete_snapshot`` inside ``DeregisterImage.do`` (https://github.com/ansible-collections/amazon.aws/pull/2444).
- ec2_transit_gateway - avoid assignment to unused ``retry_decorator`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- ec2_vpc_egress_igw - avoid assignment to unused ``vpc_id`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- ec2_vpc_nacl - avoid assignment to unused ``result`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- ec2_vpc_vpn - minor linting fixups (https://github.com/ansible-collections/amazon.aws/pull/2444).
- iam_password_policy - avoid assignment to unused variable in except block (https://github.com/ansible-collections/amazon.aws/pull/2464).
- iam_role - avoid assignment to unused variable in except block (https://github.com/ansible-collections/amazon.aws/pull/2464).
- inventory/aws_ec2 - Support jinja2 expression in ``hostnames`` variable(https://github.com/ansible-collections/amazon.aws/issues/2402).
- kms_key - avoid assignment to unused variable in except block (https://github.com/ansible-collections/amazon.aws/pull/2464).
- lambda - avoid assignment to unused ``architecture`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- lambda - avoid assignment to unused ``required_by`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- module_utils._s3 - explicitly cast super to the parent type (https://github.com/ansible-collections/amazon.aws/pull/2497).
- module_utils.botocore - avoid assigning unused parts of exc_info return (https://github.com/ansible-collections/amazon.aws/pull/2497).
- module_utils.exceptions - avoid assigning unused parts of exc_info return (https://github.com/ansible-collections/amazon.aws/pull/2497).
- module_utils.iam - avoid assignment to unused ``result`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- module_utils.s3 - avoid assignment to unused ``endpoint`` variable (https://github.com/ansible-collections/amazon.aws/pull/2464).
- plugin_utils/inventory - Add ``filters`` to list of templatable inventory options (https://github.com/ansible-collections/amazon.aws/pull/2379)
- route53 - Add support for type ``SSHFP`` records (https://github.com/ansible-collections/amazon.aws/pull/2430).
- route53_zone - Add support for enabling DNSSEC signing in a specific hosted zone (https://github.com/ansible-collections/amazon.aws/issues/1976).
- route53_zone - avoid assignmenta to unused ``current_vpc_ids`` and ``current_vpc_regions`` variables (https://github.com/ansible-collections/amazon.aws/pull/2464).
- s3_bucket - avoid assignment to unused variable in except block (https://github.com/ansible-collections/amazon.aws/pull/2464).
- s3_bucket - avoid redefining ``id`` inside ``handle_bucket_inventory`` and ``delete_bucket_inventory`` (https://github.com/ansible-collections/amazon.aws/pull/2444).
- s3_object - avoid redefining ``key_check`` inside ``_head_object`` (https://github.com/ansible-collections/amazon.aws/pull/2444).
- s3_object - simplify ``path_check`` logic (https://github.com/ansible-collections/amazon.aws/pull/2444).
- s3_object - use the ``copy`` rather than ``copy_object`` method when performing an S3 to S3 copy (https://github.com/ansible-collections/amazon.aws/issues/2117).
- s3_object_info - add support to list objects under a specific prefix (https://github.com/ansible-collections/amazon.aws/issues/2477).
- s3_object_info - avoid assignment to unused variable in except block (https://github.com/ansible-collections/amazon.aws/pull/2464).

Bugfixes
--------

- ec2_instance - Fix issue where EC2 instance module failed to apply security groups when both ``network`` and ``vpc_subnet_id`` were specified, caused by passing ``None`` to discover_security_groups() (https://github.com/ansible-collections/amazon.aws/pull/2488).
- ec2_vpc_nacl_info - Fix failure when listing NetworkACLs and no ACLs are found (https://github.com/ansible-collections/amazon.aws/issues/2425).
- iam_access_key - add missing requirements checks (https://github.com/ansible-collections/amazon.aws/pull/2465).
- module_utils.botocore - fixed type aliasing (https://github.com/ansible-collections/amazon.aws/pull/2497).
- plugin_utils.botocore - fixed type aliasing (https://github.com/ansible-collections/amazon.aws/pull/2497).
- s3_bucket - Do not use default region as location constraint when creating bucket on ceph cluster (https://github.com/ansible-collections/amazon.aws/issues/2420).

New Modules
-----------

- route53_key_signing_key - Manages a key-signing key (KSK)

v9.1.1
======

Release Summary
---------------

This release includes bug fixes for the cloudformation, ec2_security_group, lambda, rds_cluster, and ec2_vpc_net modules as well as one for the ec2 module_util.

Bugfixes
--------

- cloudformation - Fix bug where termination protection is not updated when create_changeset=true is used for stack updates (https://github.com/ansible-collections/amazon.aws/pull/2391).
- ec2_security_group - Fix the diff mode issue when creating a security group containing a rule with a managed prefix list (https://github.com/ansible-collections/amazon.aws/issues/2373).
- ec2_vpc_net - handle ipv6_cidr ``false`` and no Ipv6CidrBlockAssociationSet in vpc (https://github.com/ansible-collections/amazon.aws/pull/2374).
- lambda - Remove non UTF-8 data (contents of Lambda ZIP file) from the module output to avoid Ansible error (https://github.com/ansible-collections/amazon.aws/issues/2386).
- module_utils/ec2 - catch error code ``InvalidElasticIpID.NotFound`` on function ``create_nat_gateway()``, sometimes the ``allocate_address`` API calls will return the ID for a new elastic IP resource before it can be consistently referenced (https://github.com/ansible-collections/amazon.aws/issues/1872).
- rds_cluster - Fix issue occurring when updating RDS cluster domain (https://github.com/ansible-collections/amazon.aws/issues/2390).

v9.1.0
======

Release Summary
---------------

This release brings several bugfixes, minor changes, a new ``rds_instance_param_group_info`` module, and some deprecations for the ``autoscaling_group`` module.

Minor Changes
-------------

- autoscaling_group - adds ``group_name`` as an alias for the ``name`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_group_info - adds ``group_name`` as an alias for the ``name`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_instance_refresh - adds ``group_name`` as an alias for the ``name`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_instance_refresh_info - adds ``group_name`` as an alias for the ``name`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2396).
- ec2_instance - Fix the issue when trying to run instances using launch template in an AWS environment where no default subnet is defined(https://github.com/ansible-collections/amazon.aws/issues/2321).
- ec2_metadata_facts - add ``ansible_ec2_instance_tags`` to return values (https://github.com/ansible-collections/amazon.aws/pull/2398).
- ec2_transit_gateway - handle empty description while deleting transit gateway (https://github.com/ansible-collections/community.aws/pull/2086).

Deprecated Features
-------------------

- autoscaling_group - the ``decrement_desired_capacity`` parameter has been deprecated and will be removed in release 14.0.0 of this collection. Management of instances attached an autoscaling group can be performed using the  ``amazon.aws.autoscaling_instance`` module (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_group - the ``replace_batch_size``, ``lc_check`` and ``lt_check`` parameters have been deprecated and will be removed in release 14.0.0 of this collection. Rolling replacement of instances in an autoscaling group can be performed using the  ``amazon.aws.autoscaling_instance_refresh`` module (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_group - the functionality provided through the ``detach_instances`` parameter has been deprecated and will be removed in release 14.0.0 of this collection. Management of instances attached an autoscaling group can be performed using the  ``amazon.aws.autoscaling_instance`` module (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_group - the functionality provided through the ``replace_all_instances`` parameter has been deprecated and will be removed in release 14.0.0 of this collection. Rolling replacement of instances in an autoscaling group can be performed using the  ``amazon.aws.autoscaling_instance_refresh`` module (https://github.com/ansible-collections/amazon.aws/pull/2396).
- autoscaling_group - the functionality provided through the ``replace_instances`` parameter has been deprecated and will be removed in release 14.0.0 of this collection. Management of instances attached an autoscaling group can be performed using the  ``amazon.aws.autoscaling_instance`` module (https://github.com/ansible-collections/amazon.aws/pull/2396).

Bugfixes
--------

- elbv2 - Fix load balancer listener comparison when DefaultActions contain any action other than forward (https://github.com/ansible-collections/amazon.aws/issues/2377).

New Modules
-----------

- rds_instance_param_group_info - Describes the RDS parameter group.

v9.0.0
======

Release Summary
---------------

This major release brings a new set of supported modules that have been promoted from community.aws, several bugfixes, minor changes and deprecated features. We also dropped support for botocore<1.31.0 and boto3<1.28.0. Due to the AWS SDKs announcing the end of support for Python less than 3.8 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/), support for Python less than 3.8 by this collection was deprecated in this release and will be removed in release 10.0.0.

Major Changes
-------------

- autoscaling_instance_refresh - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.autoscaling_instance_refresh`` (https://github.com/ansible-collections/amazon.aws/pull/2338).
- autoscaling_instance_refresh_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.autoscaling_instance_refresh_info`` (https://github.com/ansible-collections/amazon.aws/pull/2338).
- ec2_launch_template - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_launch_template`` (https://github.com/ansible-collections/amazon.aws/pull/2348).
- ec2_placement_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_placement_group``.
- ec2_placement_group_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_placement_group_info``.
- ec2_transit_gateway - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_transit_gateway``.
- ec2_transit_gateway_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_transit_gateway_info``.
- ec2_transit_gateway_vpc_attachment - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_transit_gateway_vpc_attachment``.
- ec2_transit_gateway_vpc_attachment_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_transit_gateway_vpc_attachment_info``.
- ec2_vpc_egress_igw - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_egress_igw`` (https://api.github.com/repos/ansible-collections/amazon.aws/pulls/2327).
- ec2_vpc_nacl - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_nacl`` (https://github.com/ansible-collections/amazon.aws/pull/2339).
- ec2_vpc_nacl_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_nacl_info`` (https://github.com/ansible-collections/amazon.aws/pull/2339).
- ec2_vpc_peer - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_peer``.
- ec2_vpc_peering_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_peering_info``.
- ec2_vpc_vgw - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_vgw``.
- ec2_vpc_vgw_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_vgw_info``.
- ec2_vpc_vpn - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_vpn``.
- ec2_vpc_vpn_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_vpc_vpn_info``.
- elb_classic_lb_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.elb_classic_lb_info``.

Minor Changes
-------------

- Add support for transit gateway vpc attachment module (https://github.com/ansible-collections/amazon.aws/pull/2314).
- Bump version of ansible-lint to minimum 24.7.0 (https://github.com/ansible-collections/amazon.aws/pull/2201).
- Move function ``determine_iam_role`` from module ``ec2_instance`` to module_utils/ec2 so that it can be used by ``community.aws.ec2_launch_template`` module (https://github.com/ansible-collections/amazon.aws/pull/2319).
- aws_az_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2163).  - aws_region_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2163).
- backup_vault - Update code to remove unnecessary return values returned as None (https://github.com/ansible-collections/amazon.aws/pull/2105).
- cloudwatchlogs_log_group_metric_filter - Add support for ``unit`` and ``dimensions`` options (https://github.com/ansible-collections/amazon.aws/pull/2286)
- ec2_ami - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2164).
- ec2_ami_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2164).
- ec2_eip - Add support to update reverse DNS record of an EIP (https://github.com/ansible-collections/amazon.aws/pull/2292).
- ec2_eip - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2165).  - ec2_eip_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2165).
- ec2_eni - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2166).
- ec2_eni_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2166).
- ec2_import_image - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2167).
- ec2_import_image_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2167).
- ec2_instance - Pass variables ``client`` and ``module`` as function arguments instead of global variables (https://github.com/ansible-collections/amazon.aws/pull/2192).
- ec2_instance - add the possibility to upgrade / downgrade existing ec2 instance type (https://github.com/ansible-collections/amazon.aws/issues/469).
- ec2_instance - refactored code to use ``AnsibleEC2Error`` and shared code from module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2192).
- ec2_instance_info - Replaced call to deprecated function ``datetime.utcnow()`` by ``datetime.now(timezone.utc)`` (https://github.com/ansible-collections/amazon.aws/pull/2192).
- ec2_instance_info - refactored code to use ``AnsibleEC2Error`` and shared code from module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2192).
- ec2_key - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2168).
- ec2_key_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2168).
- ec2_security_group - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2169).
- ec2_security_group_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2169).
- ec2_snapshot - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_snapshot_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_spot_instance - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_spot_instance_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_vol - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2170).
- ec2_vol_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2170).
- ec2_vpc_dhcp_option - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2097).
- ec2_vpc_dhcp_option_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2097).
- ec2_vpc_endpoint - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2097).
- ec2_vpc_endpoint_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2097).
- ec2_vpc_endpoint_service_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2097).
- ec2_vpc_igw - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_vpc_igw_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_vpc_nat_gateway - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_vpc_nat_gateway_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2099).
- ec2_vpc_net - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2158).
- ec2_vpc_net_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2158).
- ec2_vpc_route_table - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2159).
- ec2_vpc_route_table - update the ec2_vpc_route_table routes parameter to support the transit gateway id (https://github.com/ansible-collections/amazon.aws/pull/2291).
- ec2_vpc_route_table_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2159).
- ec2_vpc_subnet - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2160).
- ec2_vpc_subnet_info - refactored code to use ``AnsibleEC2Error`` as well as moving shared code into module_utils.ec2 (https://github.com/ansible-collections/amazon.aws/pull/2160).
- module_utils.botocore - replace use of ``botocore.Session`` with ``boto3.Session`` for consistency (https://github.com/ansible-collections/amazon.aws/pull/2157).
- module_utils.botocore - the ``boto3_conn`` method now catches ``BotoCoreError`` rather than an incomplete list of subclasses (https://github.com/ansible-collections/amazon.aws/pull/2157).
- module_utils/autoscaling - create utils to handle AWS call for the ``autoscaling`` client (https://github.com/ansible-collections/amazon.aws/pull/2301).
- module_utils/ec2 - add some shared code for Launch template AWS API calls (https://github.com/ansible-collections/amazon.aws/pull/2319).
- module_utils/ec2 - add utils for the ec2_placement_group* modules (https://github.com/ansible-collections/amazon.aws/pull/2322).
- module_utils/ec2 - add utils for the ec2_transit_gateway_* modules (https://github.com/ansible-collections/amazon.aws/pull/2325).
- module_utils/ec2 - add utils for the ec2_vpc_peer* modules (https://github.com/ansible-collections/amazon.aws/pull/2303).
- module_utils/ec2 - add utils for the ec2_vpc_vgw_* modules (https://github.com/ansible-collections/amazon.aws/pull/2331).
- module_utils/ec2 - add utils for the ec2_vpc_vpn* modules (https://github.com/ansible-collections/amazon.aws/pull/2312).
- module_utils/ec2 - move shared code for ec2 client (https://github.com/ansible-collections/amazon.aws/pull/2302).
- module_utils/elbv2 - Refactor listeners and rules comparison logic (https://github.com/ansible-collections/amazon.aws/issues/1981).
- module_utils/rds.py - Add shared functionality from rds snapshot modules (https://github.com/ansible-collections/amazon.aws/pull/2138).
- module_utils/rds.py - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2119).
- plugin_utils.botocore - the ``boto3_conn`` method now catches ``BotoCoreError`` rather than an incomplete list of subclasses (https://github.com/ansible-collections/amazon.aws/pull/2157).
- rds_cluster_snapshot - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2138).
- rds_instance - Add support for  Multi-Tenant CDB Databases(https://github.com/ansible-collections/amazon.aws/pull/2275).
- rds_instance - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2119).
- rds_instance - Remove shared functioanlity added to module_utils/rds.py (https://github.com/ansible-collections/amazon.aws/pull/2138).
- rds_instance_info - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2119).
- rds_instance_info - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2138).
- rds_instance_snapshot - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2138).
- rds_snapshot_info - Refactor shared boto3 client functionality, add type hinting and function docstrings (https://github.com/ansible-collections/amazon.aws/pull/2138).
- s3_object_info - Added support for ``max_keys`` and ``marker`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2328).

Breaking Changes / Porting Guide
--------------------------------

- The amazon.aws collection has dropped support for ``botocore<1.31.0`` and ``boto3<1.28.0``. Most modules will continue to work with older versions of the AWS SDK.  However, compatability with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/2161).
- aws_ec2 - the parameter ``include_extra_api_calls`` was previously deprecated and has been removed (https://github.com/ansible-collections/amazon.aws/pull/2320).
- iam_policy - the ``policies`` return key was previously deprecated and has been removed, please use ``policy_names`` instead (https://github.com/ansible-collections/amazon.aws/pull/2320).
- module_utils.botocore - ``boto3_conn``'s  ``conn_type`` parameter is now mandatory (https://github.com/ansible-collections/amazon.aws/pull/2157).

Deprecated Features
-------------------

- amazon.aws collection - due to the AWS SDKs announcing the end of support for Python less than 3.8 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/) support for Python less than 3.8 by this collection has been deprecated and will removed in release 10.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2161).
- ec2_vpc_peer - the ``ec2_vpc_peer`` module has been renamed to ``ec2_vpc_peering``. The usage of the module has not changed. The ec2_vpc_peer alias will be removed in version 13.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2356).
- ec2_vpc_peering_info - ``result`` return key has been deprecated and will be removed in release 11.0.0.  Use the ``vpc_peering_connections`` return key instead (https://github.com/ansible-collections/amazon.aws/pull/2359).
- s3_object - Support for ``mode=list`` has been deprecated.  ``amazon.aws.s3_object_info`` should be used instead (https://github.com/ansible-collections/amazon.aws/pull/2328).

Bugfixes
--------

- aws_ec2 - fix SSM inventory collection for multiple (>40) hosts  (https://github.com/ansible-collections/amazon.aws/pull/2227).
- ec2_vol - output volume informations when volume exists in check mode (https://github.com/ansible-collections/amazon.aws/pull/2133).
- s3_bucket - Fixes Python 3.7 compilation issue due to addition of typing information (https://github.com/ansible-collections/amazon.aws/issues/2287).
- s3_object - Fixed an issue where ``max_keys`` was not respected (https://github.com/ansible-collections/amazon.aws/pull/2328).

New Modules
-----------

- autoscaling_instance - manage instances associated with AWS AutoScaling Groups (ASGs)
- autoscaling_instance_info - describe instances associated with AWS AutoScaling Groups (ASGs)
- ec2_launch_template_info - Gather information about launch templates and versions
- ec2_vpc_egress_igw_info - Gather information about AWS VPC Egress Only Internet gateway

v8.2.3
======

Release Summary
---------------

This release includes bugfixes for the  ``ec2_instance`` and ``s3_bucket`` modules.

Bugfixes
--------

- ec2_instance - Fix issue where EC2 instance module failed to apply security groups when both ``network`` and ``vpc_subnet_id`` were specified, caused by passing ``None`` to discover_security_groups() (https://github.com/ansible-collections/amazon.aws/pull/2488).
- s3_bucket - Do not use default region as location constraint when creating bucket on ceph cluster (https://github.com/ansible-collections/amazon.aws/issues/2420).

v8.2.2
======

Release Summary
---------------

This release includes bugfixes for the aws_ec2 inventory plugin and the cloudformation, ec2_security_group, ec2_vol, ec2_vpc_net, lambda, rds_cluster, and s3_bucket modules.

Bugfixes
--------

- aws_ec2 - fix SSM inventory collection for multiple (>40) hosts  (https://github.com/ansible-collections/amazon.aws/pull/2227).
- cloudformation - Fix bug where termination protection is not updated when create_changeset=true is used for stack updates (https://github.com/ansible-collections/amazon.aws/pull/2391).
- ec2_security_group - Fix the diff mode issue when creating a security group containing a rule with a managed prefix list (https://github.com/ansible-collections/amazon.aws/issues/2373).
- ec2_vol - output volume informations when volume exists in check mode (https://github.com/ansible-collections/amazon.aws/pull/2133).
- ec2_vpc_net - handle ipv6_cidr ``false`` and no Ipv6CidrBlockAssociationSet in vpc (https://github.com/ansible-collections/amazon.aws/pull/2374).
- lambda - Remove non UTF-8 data (contents of Lambda ZIP file) from the module output to avoid Ansible error (https://github.com/ansible-collections/amazon.aws/issues/2386).
- rds_cluster - Fix issue occurring when updating RDS cluster domain (https://github.com/ansible-collections/amazon.aws/issues/2390).
- s3_bucket - Fixes Python 3.7 compilation issue due to addition of typing information (https://github.com/ansible-collections/amazon.aws/issues/2287).

v8.2.1
======

Release Summary
---------------

This is a bugfix release for the ``iam_role`` module that resolves the issue where IAM instance profiles were being created when ``create_instance_profile`` was set to ``false`` and addresses the ``EntityAlreadyExists`` exception when the instance profile already existed.

Bugfixes
--------

- iam_role - fixes ``EntityAlreadyExists`` exception when ``create_instance_profile`` was set to ``false`` and the instance profile already existed (https://github.com/ansible-collections/amazon.aws/issues/2102).
- iam_role - fixes issue where IAM instance profiles were created when ``create_instance_profile`` was set to ``false`` (https://github.com/ansible-collections/amazon.aws/issues/2281).

v8.2.0
======

Release Summary
---------------

The amazon.aws 8.2.0 release includes a number of bugfixes, some new features and improvements. This releases also introduces a deprecation for the ``amazon.aws.iam_role`` module, where support for creating and deleting IAM instance profiles using the ``create_instance_profile`` and ``delete_instance_profile`` options has been deprecated and will be removed in a release after 2026-05-01.

Minor Changes
-------------

- cloudwatch_metric_alarm - add  support for ``evaluate_low_sample_count_percentile`` parameter.
- cloudwatch_metric_alarm - support DatapointsToAlarm config (https://github.com/ansible-collections/amazon.aws/pull/2196).
- ec2_ami - Add support for uefi-preferred boot mode (https://github.com/ansible-collections/amazon.aws/pull/2253).
- ec2_instance - Add support for ``network_interfaces`` and ``network_interfaces_ids`` options replacing deprecated option ``network`` (https://github.com/ansible-collections/amazon.aws/pull/2123).
- ec2_instance - ``network.source_dest_check`` option has been deprecated and replaced by new option ``source_dest_check`` (https://github.com/ansible-collections/amazon.aws/pull/2123).
- ec2_instance - add the possibility to create instance with multiple network interfaces (https://github.com/ansible-collections/amazon.aws/pull/2123).
- ec2_metadata_facts - Add parameter ``metadata_token_ttl_seconds`` (https://github.com/ansible-collections/amazon.aws/pull/2209).
- rds_cluster - Add support for I/O-Optimized storage configuration for aurora clusters (https://github.com/ansible-collections/amazon.aws/pull/2063).
- rds_instance - snake case for parameter ``performance_insights_kms_key_id`` was incorrect according to boto documentation (https://github.com/ansible-collections/amazon.aws/pull/2163).
- s3_bucket - Add support for bucket inventories (https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html)
- s3_object - Add support for ``expected_bucket_owner`` option (https://github.com/ansible-collections/amazon.aws/issues/2114).
- ssm parameter lookup - add new option ``droppath`` to drop the hierarchical search path from ssm parameter lookup results (https://github.com/ansible-collections/amazon.aws/pull/1756).

Deprecated Features
-------------------

- iam_role - support for creating and deleting IAM instance profiles using the ``create_instance_profile`` and ``delete_instance_profile`` options has been deprecated and will be removed in a release after 2026-05-01.  To manage IAM instance profiles the ``amazon.aws.iam_instance_profile`` module can be used instead (https://github.com/ansible-collections/amazon.aws/pull/2221).

Bugfixes
--------

- cloudwatch_metric_alarm - Fix idempotency when creating cloudwatch metric alarm without dimensions (https://github.com/ansible-collections/amazon.aws/pull/1865).
- ec2_instance - fix state processing when exact_count is used (https://github.com/ansible-collections/amazon.aws/pull/1659).
- rds_cluster - Limit params sent to api call to DBClusterIdentifier when using state started or stopped (https://github.com/ansible-collections/amazon.aws/issues/2197).
- route53 - modify the return value to return diff only when ``module._diff`` is set to true (https://github.com/ansible-collections/amazon.aws/pull/2136).
- s3_bucket - catch ``UnsupportedArgument`` when calling API ``GetBucketAccelerationConfig`` on region where it is not supported (https://github.com/ansible-collections/amazon.aws/issues/2180).
- s3_bucket - change the default behaviour of the new ``accelerate_enabled`` option to only update the configuration if explicitly passed (https://github.com/ansible-collections/amazon.aws/issues/2220).
- s3_bucket - fixes ``MethodNotAllowed`` exceptions caused by fetching transfer acceleration state in regions that don't support it (https://github.com/ansible-collections/amazon.aws/issues/2266).
- s3_bucket - fixes ``TypeError: cannot unpack non-iterable NoneType object`` errors related to bucket versioning, policies, tags or encryption (https://github.com/ansible-collections/amazon.aws/pull/2228).

v8.1.0
======

Release Summary
---------------

This release includes several documentation improvements and two new features for the ``s3_bucket`` module.

Minor Changes
-------------

- s3_bucket - Add ``object_lock_default_retention`` to set Object Lock default retention configuration for S3 buckets (https://github.com/ansible-collections/amazon.aws/pull/2062).
- s3_bucket - Add support for enabling Amazon S3 Transfer Acceleration by setting the ``accelerate_enabled`` option (https://github.com/ansible-collections/amazon.aws/pull/2046).

v8.0.1
======

Release Summary
---------------

This release includes some bug fixes for the ``s3_object``, ``ec2_instance`` and ``backup_plan_info`` modules.

Bugfixes
--------

- backup_plan_info - Bugfix to enable getting info of all backup plans (https://github.com/ansible-collections/amazon.aws/pull/2083).
- ec2_instance - do not ignore IPv6 addresses when a single network interface is specified (https://github.com/ansible-collections/amazon.aws/pull/1979).
- s3_object - fixed issue which was causing ``MemoryError`` exceptions when downloading large files (https://github.com/ansible-collections/amazon.aws/issues/2107).

v8.0.0
======

Release Summary
---------------

This major release brings several new features, bug fixes, and deprecated features. It also includes the removal of some functionality for ``iam_role, iam_role_info`` and ``module_utils.policy`` that were previously deprecated. We have also removed support for ``ansible-core<2.15``.

Minor Changes
-------------

- autoscaling_group - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).
- cloudformation - apply automatic retries when paginating through stack events without a filter (https://github.com/ansible-collections/amazon.aws/pull/2049).
- cloudtrail - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).
- ec2_instance - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).
- ec2_vol - Ensure volume state is not one of ``deleted`` or ``deleting`` when trying to delete volume, to guaranty idempotency (https://github.com/ansible-collections/amazon.aws/pull/2052).
- ec2_vol - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).
- elb_classic_lb - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).
- kms_key - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).
- lambda_event - Add support for setting the ``maximum_batching_window_in_seconds`` option (https://github.com/ansible-collections/amazon.aws/pull/2025).
- module_uils/botocore - support sets and tuples of errors as well as lists (https://github.com/ansible-collections/amazon.aws/pull/1829).
- module_utils/elbv2 - Add support for adding listener with multiple certificates during ALB creation. Allows elb_application_elb module to handle mentioned use case. (https://github.com/ansible-collections/amazon.aws/pull/1950).
- module_utils/elbv2 - Add the possibility to update ``SslPolicy``, ``Certificates`` and ``AlpnPolicy`` for TLS listeners (https://github.com/ansible-collections/amazon.aws/issues/1198).
- rds_instance - Allow passing empty list to ``enable_cloudwatch_logs_exports`` in order to remove all existing exports (https://github.com/ansible-collections/amazon.aws/pull/1917).
- s3_bucket - refactor s3_bucket module code for improved readability and maintainability (https://github.com/ansible-collections/amazon.aws/pull/2057).
- s3_object - removed unused code (https://github.com/ansible-collections/amazon.aws/pull/1996).

Breaking Changes / Porting Guide
--------------------------------

- amazon.aws collection - Support for ansible-core < 2.15 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/2093).
- iam_role - ``iam_role.assume_role_policy_document`` is no longer converted from CamelCase to snake_case (https://github.com/ansible-collections/amazon.aws/pull/2040).
- iam_role_info - ``iam_role.assume_role_policy_document`` is no longer converted from CamelCase to snake_case (https://github.com/ansible-collections/amazon.aws/pull/2040).
- kms_key - the ``policies`` return value has been renamed to ``key_policies`` the contents has not been changed (https://github.com/ansible-collections/amazon.aws/pull/2040).
- kms_key_info - the ``policies`` return value has been renamed to ``key_policies`` the contents has not been changed (https://github.com/ansible-collections/amazon.aws/pull/2040).
- lambda_event - | ``batch_size`` no longer defaults to 100. According to the boto3 API (https://boto3.amazonaws.com/v1/documentation/api/1.26.78/reference/services/lambda.html#Lambda.Client.create_event_source_mapping), ``batch_size`` defaults to 10 for sqs sources and to 100 for stream sources (https://github.com/ansible-collections/amazon.aws/pull/2025).

Deprecated Features
-------------------

- aws_ec2 inventory plugin - removal of the previously deprecated ``include_extra_api_calls`` option has been assigned to release 9.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2040).
- cloudformation - the ``template`` parameter has been deprecated and will be removed in a release after 2026-05-01.  The ``template_body`` parameter can be used in conjungtion with the lookup plugin (https://github.com/ansible-collections/amazon.aws/pull/2048).
- iam_policy - removal of the previously deprecated ``policies`` return key has been assigned to release 9.0.0.  Use the ``policy_names`` return key instead (https://github.com/ansible-collections/amazon.aws/pull/2040).
- module_utils.botocore - the ``boto3`` parameter for ``get_aws_connection_info()`` will be removed in a release after 2025-05-01. The ``boto3`` parameter has been ignored since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2047).
- module_utils.botocore - the ``boto3`` parameter for ``get_aws_region()`` will be removed in a release after 2025-05-01. The ``boto3`` parameter has been ignored since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2047).
- module_utils.ec2 - the ``boto3`` parameter for ``get_ec2_security_group_ids_from_names()`` will be removed in a release after 2025-05-01. The ``boto3`` parameter has been ignored since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2047).
- rds_param_group - the ``rds_param_group`` module has been renamed to ``rds_instance_param_group``. The usage of the module has not changed. The rds_param_group alias will be removed in version 10.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2058).

Removed Features (previously deprecated)
----------------------------------------

- iam_role - the ``iam_role.assume_role_policy_document_raw`` return value has been deprecated.  ``iam_role.assume_role_policy_document`` now returns the same format as ``iam_role.assume_role_policy_document_raw`` (https://github.com/ansible-collections/amazon.aws/pull/2040).
- iam_role_info - the ``iam_role.assume_role_policy_document_raw`` return value has been deprecated.  ``iam_role.assume_role_policy_document`` now returns the same format as ``iam_role.assume_role_policy_document_raw`` (https://github.com/ansible-collections/amazon.aws/pull/2040).
- module_utils.policy - the previously deprecated ``sort_json_policy_dict()`` function has been removed, consider using ``compare_policies()`` instead (https://github.com/ansible-collections/amazon.aws/pull/2052).

Bugfixes
--------

- elb_classic_lb - fixes bug where ``proxy_protocol`` not being set or being set to ``None`` may result in unexpected behaviour or errors (https://github.com/ansible-collections/amazon.aws/pull/2049).
- lambda_event - Fix when ``batch_size`` is greater than 10, by enabling support for setting ``maximum_batching_window_in_seconds`` (https://github.com/ansible-collections/amazon.aws/pull/2025).
- lambda_event - Retrieve function ARN using AWS API (get_function) instead of building it with AWS account information (https://github.com/ansible-collections/amazon.aws/issues/1859).

v7.6.1
======

Release Summary
---------------

This release includes some bug fixes for the ``ec2_instance`` and ``backup_plan_info`` modules.

Bugfixes
--------

- backup_plan_info - Bugfix to enable getting info of all backup plans (https://github.com/ansible-collections/amazon.aws/pull/2083).
- ec2_instance - do not ignore IPv6 addresses when a single network interface is specified (https://github.com/ansible-collections/amazon.aws/pull/1979).

v7.6.0
======

Release Summary
---------------

This release brings several bugfixes, minor changes and some new rds modules (``rds_cluster_param_group``, ``rds_cluster_param_group_info`` and ``rds_engine_versions_info``). It also introduces a deprecation for the ``cloudformation`` module.

Minor Changes
-------------

- ec2_instance - add support for ``host`` option in placement.tenancy (https://github.com/ansible-collections/amazon.aws/pull/2026).
- ec2_vol - Ensure volume state is not one of ``deleted`` or ``deleting`` when trying to delete volume, to guaranty idempotency (https://github.com/ansible-collections/amazon.aws/pull/2052).

Deprecated Features
-------------------

- cloudformation - the ``template`` parameter has been deprecated and will be removed in a release after 2026-05-01.  The ``template_body`` parameter can be used in conjungtion with the lookup plugin (https://github.com/ansible-collections/amazon.aws/pull/2048).
- module_utils.botocore - the ``boto3`` parameter for ``get_aws_connection_info()`` will be removed in a release after 2025-05-01. The ``boto3`` parameter has been ignored since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2047).
- module_utils.botocore - the ``boto3`` parameter for ``get_aws_region()`` will be removed in a release after 2025-05-01. The ``boto3`` parameter has been ignored since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2047).
- module_utils.ec2 - the ``boto3`` parameter for ``get_ec2_security_group_ids_from_names()`` will be removed in a release after 2025-05-01. The ``boto3`` parameter has been ignored since release 4.0.0 (https://github.com/ansible-collections/amazon.aws/pull/2047).

Bugfixes
--------

- iam_managed_policy - fixes bug that causes ``ParamValidationError`` when attempting to delete a policy that's attached to a role or a user (https://github.com/ansible-collections/amazon.aws/issues/2067).
- iam_role_info - fixes bug in handling paths missing the ``/`` prefix and/or suffix (https://github.com/ansible-collections/amazon.aws/issues/2065).
- s3_object - fix idempotency issue when copying object uploaded using multipart upload (https://github.com/ansible-collections/amazon.aws/issues/2016).

New Modules
-----------

- rds_cluster_param_group - Manage RDS cluster parameter groups
- rds_cluster_param_group_info - Describes the properties of specific RDS cluster parameter group.
- rds_engine_versions_info - Describes the properties of specific versions of DB engines.

v7.5.0
======

Release Summary
---------------

This release includes a new feature for the ``iam_user_info`` module, bugfixes for the ``cloudwatchlogs_log_group_info`` and ``s3_object`` modules and the inventory plugins, and some internal refactoring of ``module_utils``.

Minor Changes
-------------

- iam_user_info - Add ``login_profile`` to return info that is get from a user, to know if they can login from AWS console (https://github.com/ansible-collections/amazon.aws/pull/2012).
- module_utils.iam - refactored normalization functions to use ``boto3_resource_to_ansible_dict()`` and ``boto3_resource_list_to_ansible_dict()`` (https://github.com/ansible-collections/amazon.aws/pull/2006).
- module_utils.transformations - add ``boto3_resource_to_ansible_dict()`` and ``boto3_resource_list_to_ansible_dict()`` helpers (https://github.com/ansible-collections/amazon.aws/pull/2006).

Bugfixes
--------

- cloudwatchlogs_log_group_info - Implement exponential backoff when making API calls to prevent throttling exceptions (https://github.com/ansible-collections/amazon.aws/issues/2011).
- plugin_utils.inventory - Ensure templated options in lookup plugins are converted (https://github.com/ansible-collections/amazon.aws/issues/1955).
- s3_object - Fix the issue when copying an object with overriding metadata. (https://github.com/ansible-collections/amazon.aws/issues/1991).

v7.4.0
======

Release Summary
---------------

This release brings several bugfixes and minor changes. It also introduces a deprecation for the ``iam_role_info`` plugin.

Minor Changes
-------------

- AnsibeAWSModule - added ``fail_json_aws_error()`` as a wrapper for ``fail_json()`` and ``fail_json_aws()`` when passed an ``AnsibleAWSError`` exception (https://github.com/ansible-collections/amazon.aws/pull/1997).
- iam_access_key - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_access_key_info - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_group - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_instance_profile - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_instance_profile_info - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_managed_policy - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_mfa_device_info - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_role - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_role_info - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_user - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).
- iam_user_info - refactored code to use ``AnsibleIAMError`` and ``IAMErrorHandler`` as well as moving shared code into module_utils.iam (https://github.com/ansible-collections/amazon.aws/pull/1998).

Deprecated Features
-------------------

- iam_role_info - in a release after 2026-05-01 paths must begin and end with ``/`` (https://github.com/ansible-collections/amazon.aws/pull/1998).

Bugfixes
--------

- cloudwatchevent_rule - Fix to avoid adding quotes to JSON input for provided input_template (https://github.com/ansible-collections/amazon.aws/pull/1883).
- lookup/secretsmanager_secret - fix the issue when the nested secret is missing and on_missing is set to warn, the lookup was raising an error instead of a warning message (https://github.com/ansible-collections/amazon.aws/issues/1781).
- module_utils/elbv2 - Fix issue when creating or modifying Load balancer rule type authenticate-oidc using ``ClientSecret`` parameter and ``UseExistingClientSecret=true`` (https://github.com/ansible-collections/amazon.aws/issues/1877).

v7.3.0
======

Release Summary
---------------

The amazon.aws 7.3.0 release includes a number of minor bugfixes, some new features and improvements.

Minor Changes
-------------

- backup_plan - Let user to set ``schedule_expression_timezone`` for backup plan rules when when using botocore >= 1.31.36 (https://github.com/ansible-collections/amazon.aws/issues/1952).
- iam_user - refactored error handling to use a decorator (https://github.com/ansible-collections/amazon.aws/pull/1951).
- lambda - added support for using ECR images for the function (https://github.com/ansible-collections/amazon.aws/pull/1939).
- module_utils.errors - added a basic error handler decorator (https://github.com/ansible-collections/amazon.aws/pull/1951).
- rds_cluster - Add support for ServerlessV2ScalingConfiguration to create and modify cluster operations (https://github.com/ansible-collections/amazon.aws/pull/1839).
- s3_bucket_info - add parameter ``bucket_versioning`` to return the versioning state of a bucket (https://github.com/ansible-collections/amazon.aws/pull/1919).
- s3_object_info - fix exception raised when listing objects from empty bucket (https://github.com/ansible-collections/amazon.aws/pull/1919).

Bugfixes
--------

- backup_plan - Fix idempotency issue when using botocore >= 1.31.36 (https://github.com/ansible-collections/amazon.aws/issues/1952).
- plugins/inventory/aws_ec2 - Fix failure when retrieving information for more than 40 instances with use_ssm_inventory (https://github.com/ansible-collections/amazon.aws/issues/1713).

v7.2.0
======

Release Summary
---------------

This release includes new features and a bugfix.

Minor Changes
-------------

- ec2_instance - Add support for modifying metadata options of an existing instance (https://github.com/ansible-collections/amazon.aws/pull/1918).
- iam_group - Basic testing of ``name`` and ``path`` has been added to improve error messages (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_group - ``group_name`` has been added as an alias to ``name`` for consistency with other IAM modules (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_instance_profile - Basic testing of ``name`` and ``path`` has been added to improve error messages (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_instance_profile - Basic testing of ``name`` and ``path`` has been added to improve error messages (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_instance_profile - attempting to change the ``path`` for an existing profile will now generate a warning, previously this was silently ignored (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_instance_profile - the ``prefix`` parameter has been renamed ``path`` for consistency with other IAM modules, ``prefix`` remains as an alias. No change to playbooks is required (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_instance_profile - the default value for ``path`` has been removed.  New instances will still be created with a default path of ``/``. No change to playbooks is required (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_managed_policy - Basic testing of ``name`` and ``path`` has been added to improve error messages (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_managed_policy - ``description`` attempting to update the description now results in a warning, previously it was simply ignored (https://github.com/ansible-collections/amazon.aws/pull/1936).
- iam_managed_policy - ``policy`` is no longer a required parameter (https://github.com/ansible-collections/amazon.aws/pull/1936).
- iam_managed_policy - added support for tagging managed policies (https://github.com/ansible-collections/amazon.aws/pull/1936).
- iam_managed_policy - more consistently perform retries on rate limiting errors (https://github.com/ansible-collections/amazon.aws/pull/1936).
- iam_managed_policy - support for setting ``path`` (https://github.com/ansible-collections/amazon.aws/pull/1936).
- iam_managed_policy - the ``policy_description`` parameter has been renamed ``description`` for consistency with other IAM modules, ``policy_description`` remains as an alias. No change to playbooks is required (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_managed_policy - the ``policy_name`` parameter has been renamed ``name`` for consistency with other IAM modules, ``policy_name`` remains as an alias. No change to playbooks is required (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role - Basic testing of ``name`` and ``path`` has been added to improve error messages (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role - ``prefix`` and ``path_prefix`` have been added as aliases to ``path`` for consistency with other IAM modules (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role - ``role_name`` has been added as an alias to ``name`` for consistency with other IAM modules (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role - attempting to change the ``path`` for an existing profile will now generate a warning, previously this was silently ignored (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role - the default value for ``path`` has been removed.  New roles will still be created with a default path of ``/``. No change to playbooks is required (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role_info - ``path`` and ``prefix`` have been added as aliases to ``path_prefix`` for consistency with other IAM modules (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_user - Basic testing of ``name`` and ``path`` has been added to improve error messages (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_user - ``user_name`` has been added as an alias to ``name`` for consistency with other IAM modules (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_user - add ``boundary`` parameter to support managing boundary policy on users (https://github.com/ansible-collections/amazon.aws/pull/1912).
- iam_user - add ``path`` parameter to support managing user path (https://github.com/ansible-collections/amazon.aws/pull/1912).
- iam_user - added ``attached_policies`` to return value (https://github.com/ansible-collections/amazon.aws/pull/1912).
- iam_user - refactored code to reduce complexity (https://github.com/ansible-collections/amazon.aws/pull/1912).
- iam_user_info - ``prefix`` has been added as an alias to ``path_prefix`` for consistency with other IAM modules (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_user_info - the ``path`` parameter has been renamed ``path_prefix`` for consistency with other IAM modules, ``path`` remains as an alias. No change to playbooks is required (https://github.com/ansible-collections/amazon.aws/pull/1933).

Bugfixes
--------

- iam_managed_policy - fixed an issue where only partial results were returned (https://github.com/ansible-collections/amazon.aws/pull/1936).

v7.1.0
======

Release Summary
---------------

This release brings some new features and several bugfixes.

Minor Changes
-------------

- autoscaling_group - minor PEP8 whitespace sanity fixes (https://github.com/ansible-collections/amazon.aws/pull/1846).
- ec2_ami_info - simplify parameters to ``get_image_attribute`` to only pass ID of image (https://github.com/ansible-collections/amazon.aws/pull/1846).
- ec2_eip - use ``ResourceTags`` to set initial tags upon creation (https://github.com/ansible-collections/amazon.aws/issues/1843)
- ec2_instance - add support for AdditionalInfo option when creating an instance (https://github.com/ansible-collections/amazon.aws/pull/1828).
- ec2_security_group - use ``ResourceTags`` to set initial tags upon creation (https://github.com/ansible-collections/amazon.aws/pull/1844)
- ec2_vpc_igw - use ``ResourceTags`` to set initial tags upon creation (https://github.com/ansible-collections/amazon.aws/issues/1843)
- ec2_vpc_route_table - use ``ResourceTags`` to set initial tags upon creation (https://github.com/ansible-collections/amazon.aws/issues/1843)
- ec2_vpc_subnet - the default value for ``tags`` has been changed from ``{}`` to ``None``, to remove tags from a subnet an empty map must be explicitly passed to the module (https://github.com/ansible-collections/amazon.aws/pull/1876).
- ec2_vpc_subnet - use ``ResourceTags`` to set initial tags upon creation (https://github.com/ansible-collections/amazon.aws/issues/1843)
- ec2_vpc_subnet - use ``wait_timeout`` to also control maximum time to wait for initial creation of subnets (https://github.com/ansible-collections/amazon.aws/pull/1848).
- iam_group - add support for setting group path (https://github.com/ansible-collections/amazon.aws/pull/1892).
- iam_group - adds attached_policies return value (https://github.com/ansible-collections/amazon.aws/pull/1892).
- iam_group - code refactored to avoid single long function (https://github.com/ansible-collections/amazon.aws/pull/1892).
- rds_instance_snapshot - minor PEP8 whitespace sanity fixes (https://github.com/ansible-collections/amazon.aws/pull/1846).

Bugfixes
--------

- ec2_vpc_subnet - cleanly handle failure when subnet isn't created in time (https://github.com/ansible-collections/amazon.aws/pull/1848).
- s3_object - Fix typo that caused false deprecation warning when setting ``overwrite=latest`` (https://github.com/ansible-collections/amazon.aws/pull/1847).
- s3_object - when doing a put and specifying ``Content-Type`` in metadata, this module (since 6.0.0) erroneously set the ``Content-Type`` to ``None`` causing the put to fail. Fix now correctly honours the specified ``Content-Type`` (https://github.com/ansible-collections/amazon.aws/issues/1881).

v7.0.0
======

Release Summary
---------------

This major release brings a new set of supported modules that have been promoted from community.aws, several bugfixes, minor changes and deprecated features. We also dropped support for ``botocore<1.29.0`` and ``boto3<1.26.0``. Due to the AWS SDKs announcing the end of support for Python less than 3.7 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/), support for Python less than 3.7 by this collection was deprecated in release 6.0.0 and removed in this release.

Major Changes
-------------

- aws_region_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.aws_region_info``.
- aws_s3_bucket_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.aws_s3_bucket_info``.
- iam_access_key - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_access_key``.
- iam_access_key_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_access_key_info``.
- iam_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_group`` (https://github.com/ansible-collections/amazon.aws/pull/1755).
- iam_managed_policy - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_managed_policy`` (https://github.com/ansible-collections/amazon.aws/pull/1762).
- iam_mfa_device_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_mfa_device_info`` (https://github.com/ansible-collections/amazon.aws/pull/1761).
- iam_password_policy - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_password_policy``.
- iam_role - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_role`` (https://github.com/ansible-collections/amazon.aws/pull/1760).
- iam_role_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_role_info`` (https://github.com/ansible-collections/amazon.aws/pull/1760).
- s3_bucket_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.s3_bucket_info``.
- sts_assume_role - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.sts_assume_role``.

Minor Changes
-------------

- amazon.aws collection - apply isort code formatting to ensure consistent formatting of code (https://github.com/ansible-collections/amazon.aws/pull/1771).
- ec2_instance - add support for additional ``placement`` options and ``license_specifications`` in run instance spec (https://github.com/ansible-collections/amazon.aws/issues/1824).
- ec2_instance_info - add new parameter ``include_attributes`` to describe instance attributes (https://github.com/ansible-collections/amazon.aws/pull/1577).
- ec2_metadata_facts - use fstrings where appropriate (https://github.com/ansible-collections/amazon.aws/pull/1802).
- ec2_vpc_igw - Add ability to attach/detach VPC to/from internet gateway (https://github.com/ansible-collections/amazon.aws/pull/1786).
- ec2_vpc_igw - Add ability to change VPC attached to internet gateway (https://github.com/ansible-collections/amazon.aws/pull/1786).
- ec2_vpc_igw - Add ability to create an internet gateway without attaching a VPC (https://github.com/ansible-collections/amazon.aws/pull/1786).
- ec2_vpc_igw - Add ability to delete a vpc internet gateway using the id of the gateway (https://github.com/ansible-collections/amazon.aws/pull/1786).
- elb_application_lb_info - add new parameters ``include_attributes``, ``include_listeners`` and  ``include_listener_rules`` to optionally speed up module by fetching less information (https://github.com/ansible-collections/amazon.aws/pull/1778).
- module_utils.botocore - migrate from vendored copy of LooseVersion to packaging.version.Version (https://github.com/ansible-collections/amazon.aws/pull/1587).
- rds_cluster - Add support for removing cluster from global db (https://github.com/ansible-collections/amazon.aws/pull/1705).
- rds_cluster - add support for another ``state`` choice called ``started``. This starts the rds cluster (https://github.com/ansible-collections/amazon.aws/pull/1647/files).
- rds_cluster - add support for another ``state`` choice called ``stopped``. This stops the rds cluster (https://github.com/ansible-collections/amazon.aws/pull/1647/files).
- route53 - add a ``wait_id`` return value when a change is done (https://github.com/ansible-collections/amazon.aws/pull/1683).
- route53_health_check - add support for a string list parameter called ``child_health_checks`` to specify health checks that must be healthy for the calculated health check (https://github.com/ansible-collections/amazon.aws/pull/1631).
- route53_health_check - add support for an integer parameter called ``health_threshold`` to specify the minimum number of healthy child health checks that must be healthy for the calculated health check (https://github.com/ansible-collections/amazon.aws/pull/1631).
- route53_health_check - add support for another ``type`` choice called ``CALCULATED`` (https://github.com/ansible-collections/amazon.aws/pull/1631).
- s3_object - Allow recursive copy of objects in S3 bucket (https://github.com/ansible-collections/amazon.aws/issues/1379).
- s3_object - use fstrings where appropriate (https://github.com/ansible-collections/amazon.aws/pull/1802).

Breaking Changes / Porting Guide
--------------------------------

- The amazon.aws collection has dropped support for ``botocore<1.29.0`` and ``boto3<1.26.0``. Most modules will continue to work with older versions of the AWS SDK, however compatability with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/1763).
- amazon.aws collection - due to the AWS SDKs announcing the end of support for Python less than 3.7 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/) support for Python less than 3.7 by this collection wss been deprecated in release 6.0.0 and removed in release 7.0.0. (https://github.com/ansible-collections/amazon.aws/pull/1763).
- module_utils - ``module_utils.urls`` was previously deprecated and has been removed (https://github.com/ansible-collections/amazon.aws/pull/1540).
- module_utils._version - vendored copy of distutils.version has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1587).

Deprecated Features
-------------------

- ec2_instance - deprecation of ``tenancy`` and ``placement_group`` in favor of ``placement`` attribute  (https://github.com/ansible-collections/amazon.aws/pull/1825).

Bugfixes
--------

- aws_ec2 inventory plugin - fix ``NoRegionError`` when no regions are provided and region isn't specified (https://github.com/ansible-collections/amazon.aws/issues/1551).
- ec2_instance - retry API call if we get ``InvalidInstanceID.NotFound`` error (https://github.com/ansible-collections/amazon.aws/pull/1650).
- ec2_vpc_route_table_info - default filters to empty dictionary (https://github.com/ansible-collections/amazon.aws/issues/1668).
- s3_bucket - fixes issue when deleting a bucket with unversioned objects (https://github.com/ansible-collections/amazon.aws/issues/1533).
- s3_object - fixed ``NoSuchTagSet`` error when S3 endpoint doesn't support tags (https://github.com/ansible-collections/amazon.aws/issues/1607).
- s3_object - fixes regression related to objects with a leading ``/`` (https://github.com/ansible-collections/amazon.aws/issues/1548).

New Modules
-----------

- ec2_import_image - Manage AWS EC2 import image tasks
- ec2_import_image_info - Gather information about import virtual machine tasks
- rds_global_cluster_info - Obtain information about Aurora global database clusters

v6.5.4
======

Release Summary
---------------

This release includes bugfixes for the ``cloudwatchlogs_log_group_info`` module and the inventory plugins.

Bugfixes
--------

- cloudwatchlogs_log_group_info - Implement exponential backoff when making API calls to prevent throttling exceptions (https://github.com/ansible-collections/amazon.aws/issues/2011).
- plugin_utils.inventory - Ensure templated options in lookup plugins are converted (https://github.com/ansible-collections/amazon.aws/issues/1955).

v6.5.3
======

Release Summary
---------------

This release includes bugfixes for the``cloudwatchevent_rule`` module and ``secretsmanager_secret`` lookup plugin.

Bugfixes
--------

- cloudwatchevent_rule - Fix to avoid adding quotes to JSON input for provided input_template (https://github.com/ansible-collections/amazon.aws/pull/1883).
- lookup/secretsmanager_secret - fix the issue when the nested secret is missing and on_missing is set to warn, the lookup was raising an error instead of a warning message (https://github.com/ansible-collections/amazon.aws/issues/1781).

v6.5.2
======

Release Summary
---------------

This release includes a bugfix for the ``amazon.aws.aws_ec2`` inventory plugin when retrieving information for more than 40 instances with ``use_ssm_inventory``.

Bugfixes
--------

- plugins/inventory/aws_ec2 - Fix failure when retrieving information for more than 40 instances with use_ssm_inventory (https://github.com/ansible-collections/amazon.aws/issues/1713).

v6.5.1
======

Release Summary
---------------

This release includes several bugfixes.

Minor Changes
-------------

- ec2_vpc_subnet - use ``wait_timeout`` to also control maximum time to wait for initial creation of subnets (https://github.com/ansible-collections/amazon.aws/pull/1848).

Bugfixes
--------

- ec2_instance - retry API call if we get ``InvalidInstanceID.NotFound`` error (https://github.com/ansible-collections/amazon.aws/pull/1650).
- ec2_vpc_subnet - cleanly handle failure when subnet isn't created in time (https://github.com/ansible-collections/amazon.aws/pull/1848).
- s3_object - Fix typo that caused false deprecation warning when setting ``overwrite=latest`` (https://github.com/ansible-collections/amazon.aws/pull/1847).
- s3_object - fixed ``NoSuchTagSet`` error when S3 endpoint doesn't support tags (https://github.com/ansible-collections/amazon.aws/issues/1607).
- s3_object - when doing a put and specifying ``Content-Type`` in metadata, this module (since 6.0.0) erroneously set the ``Content-Type`` to ``None`` causing the put to fail. Fix now correctly honours the specified ``Content-Type`` (https://github.com/ansible-collections/amazon.aws/issues/1881).

v6.5.0
======

Release Summary
---------------

This release is the last planned minor release of ``amazon.aws`` prior to the release of 7.0.0.
It includes documentation fixes as well as minor changes and bug fixes for the ``ec2_ami`` and ``elb_application_lb_info`` modules.

Minor Changes
-------------

- ec2_ami - add support for ``org_arns`` and ``org_unit_arns`` in launch_permissions (https://github.com/ansible-collections/amazon.aws/pull/1690).
- elb_application_lb_info - drop redundant ``describe_load_balancers`` call fetching ``ip_address_type`` (https://github.com/ansible-collections/amazon.aws/pull/1768).

Bugfixes
--------

- elb_application_lb_info - ensure all API queries use the retry decorator (https://github.com/ansible-collections/amazon.aws/issues/1767).

v6.4.0
======

Release Summary
---------------

This release brings a new module named ``amazon.aws.ec2_key_info``, some documentation improvements, new features and bugfixes.

Minor Changes
-------------

- cloudformation - Add support for ``disable_rollback`` to update stack operation (https://github.com/ansible-collections/amazon.aws/issues/1681).
- ec2_key - add support for new parameter ``file_name`` to save private key in when new key is created by AWS. When this option is provided the generated private key will be removed from the module return (https://github.com/ansible-collections/amazon.aws/pull/1704).

Bugfixes
--------

- backup_selection - ensures that updating an existing selection will add new ``Conditions`` if there previously were not any (https://github.com/ansible-collections/amazon.aws/pull/1701).

New Modules
-----------

- ec2_key_info - Gather information about EC2 key pairs in AWS

v6.3.0
======

Release Summary
---------------

This release brings some new features and several bugfixes.

Minor Changes
-------------

- rds_cluster - add support for another ``state`` choice called ``started``. This starts the rds cluster (https://github.com/ansible-collections/amazon.aws/pull/1647/files).
- rds_cluster - add support for another ``state`` choice called ``stopped``. This stops the rds cluster (https://github.com/ansible-collections/amazon.aws/pull/1647/files).
- route53 - add a ``wait_id`` return value when a change is done (https://github.com/ansible-collections/amazon.aws/pull/1683).
- route53_health_check - add support for a string list parameter called ``child_health_checks`` to specify health checks that must be healthy for the calculated health check (https://github.com/ansible-collections/amazon.aws/pull/1631).
- route53_health_check - add support for an integer parameter called ``health_threshold`` to specify the minimum number of healthy child health checks that must be healthy for the calculated health check (https://github.com/ansible-collections/amazon.aws/pull/1631).
- route53_health_check - add support for another ``type`` choice called ``CALCULATED`` (https://github.com/ansible-collections/amazon.aws/pull/1631).

Bugfixes
--------

- ec2_vpc_route_table_info - default filters to empty dictionary (https://github.com/ansible-collections/amazon.aws/issues/1668).
- rds_cluster - Add ``AllocatedStorage``, ``DBClusterInstanceClass``, ``StorageType``, ``Iops``, and ``EngineMode`` to the list of parameters that can be passed when creating or modifying a Multi-AZ RDS cluster (https://github.com/ansible-collections/amazon.aws/pull/1657).
- rds_cluster - Allow to pass GlobalClusterIdentifier to rds cluster on creation (https://github.com/ansible-collections/amazon.aws/pull/1663).

v6.2.0
======

Release Summary
---------------

This release brings some new modules, features, and several bugfixes.

Minor Changes
-------------

- backup_selection - add validation and documentation for all conditions suboptions (https://github.com/ansible-collections/amazon.aws/pull/1633).
- ec2_instance - refactored ARN validation handling (https://github.com/ansible-collections/amazon.aws/pull/1619).
- iam_user - refactored ARN validation handling (https://github.com/ansible-collections/amazon.aws/pull/1619).
- module_utils.arn - add ``resource_id`` and ``resource_type`` to ``parse_aws_arn`` return values (https://github.com/ansible-collections/amazon.aws/pull/1619).
- module_utils.arn - added ``validate_aws_arn`` function to handle common pattern matching for ARNs (https://github.com/ansible-collections/amazon.aws/pull/1619).

Bugfixes
--------

- backup_plan - Use existing ``scrub_none_values`` function from module_utils to remove None values from nested dicts in supplied params. Nested None values were being retained and causing an error when sent through to the boto3 client operation (https://github.com/ansible-collections/amazon.aws/pull/1611).
- backup_vault - fix error when updating tags on a backup vault by using the correct boto3 client methods for tagging and untagging backup resources (https://github.com/ansible-collections/amazon.aws/pull/1610).
- cloudwatchevent_rule - Fixes changed status to report False when no change has been made. The module had incorrectly always reported a change. (https://github.com/ansible-collections/amazon.aws/pull/1589)
- ec2_vpc_nat_gateway - adding a boolean parameter called ``default_create`` to allow users to have the option to choose whether they want to display an error message or create a NAT gateway when an EIP address is not found. The module (ec2_vpc_nat_gateway) had incorrectly failed silently if EIP didn't exist (https://github.com/ansible-collections/amazon.aws/issues/1295).
- ec2_vpc_nat_gateway - fixes to nat gateway so that when the user creates a private NAT gateway, an Elastic IP address should not be allocated. The module had inncorrectly always allocate elastic IP address when creating private nat gateway (https://github.com/ansible-collections/amazon.aws/pull/1632).
- lambda_execute - Fixes to the stack trace output, where it does not contain spaces between each character. The module had incorrectly always outputted extra spaces between each character. (https://github.com/ansible-collections/amazon.aws/pull/1615)
- module_utils.backup - get_selection_details fix empty list returned when multiple backup selections exist (https://github.com/ansible-collections/amazon.aws/pull/1633).

New Modules
-----------

- iam_instance_profile - manage IAM instance profiles
- iam_instance_profile_info - gather information on IAM instance profiles

v6.1.0
======

Release Summary
---------------

This release brings some new features, several bugfixes, and deprecated features are also included.

Minor Changes
-------------

- ec2_snapshot - Add support for modifying createVolumePermission (https://github.com/ansible-collections/amazon.aws/pull/1464).
- ec2_snapshot_info - Add createVolumePermission to output result (https://github.com/ansible-collections/amazon.aws/pull/1464).

Deprecated Features
-------------------

- s3_object - support for passing object keys with a leading ``/`` has been deprecated and will be removed in a release after 2025-12-01 (https://github.com/ansible-collections/amazon.aws/pull/1549).

Bugfixes
--------

- autoscaling_group - fix ValidationError when describing an autoscaling group that has more than 20 target groups attached to it by breaking the request into chunks (https://github.com/ansible-collections/amazon.aws/pull/1593).
- autoscaling_group_info - fix ValidationError when describing an autoscaling group that has more than 20 target groups attached to it by breaking the request into chunks (https://github.com/ansible-collections/amazon.aws/pull/1593).
- ec2_instance - fix check_mode issue when adding network interfaces (https://github.com/ansible-collections/amazon.aws/issues/1403).
- ec2_metadata_facts - Handle decompression when EC2 instance user-data is gzip compressed. The fetch_url method from ansible.module_utils.urls does not decompress the user-data unless the header explicitly contains ``Content-Encoding: gzip`` (https://github.com/ansible-collections/amazon.aws/pull/1575).
- elb_application_lb - fix missing attributes on creation of ALB. The ``create_or_update_alb()`` was including ALB-specific attributes when updating an existing ALB but not when creating a new ALB (https://github.com/ansible-collections/amazon.aws/issues/1510).
- module_utils.acm - fixes list_certificates returning only RSA_2048 certificates (https://github.com/ansible-collections/amazon.aws/issues/1567).
- rds_instance - add support for CACertificateIdentifier to create/update rds instance (https://github.com/ansible-collections/amazon.aws/pull/1459).

v6.0.1
======

Release Summary
---------------

This is a patch release that includes some bug fixes for the aws_ec2 inventory plugin and the s3_bucket and s3_object modules.

Bugfixes
--------

- aws_ec2 inventory plugin - fix ``NoRegionError`` when no regions are provided and region isn't specified (https://github.com/ansible-collections/amazon.aws/issues/1551).
- s3_bucket - fixes issue when deleting a bucket with unversioned objects (https://github.com/ansible-collections/amazon.aws/issues/1533).
- s3_object - fixes regression related to objects with a leading ``/`` (https://github.com/ansible-collections/amazon.aws/issues/1548).

v6.0.0
======

Release Summary
---------------

This release brings some new plugins and features. Several bugfixes, breaking changes and deprecated features are also included. The amazon.aws collection has dropped support for ``botocore<1.25.0`` and ``boto3<1.22.0``. Support for Python 3.6 has also been dropped.

Minor Changes
-------------

- Add github actions to run unit and sanity tests.(https://github.com/ansible-collections/amazon.aws/pull/1393).
- AnsibleAWSModule - add support to the ``client`` and ``resource`` methods for overriding the default parameters (https://github.com/ansible-collections/amazon.aws/pull/1303).
- CONTRIBUTING.md - refactors and adds to contributor documentation (https://github.com/ansible-collections/amazon.aws/issues/924)
- Refactor inventory plugins and add aws_rds inventory unit tests (https://github.com/ansible-collections/amazon.aws/pull/1218).
- Refactor module_utils/cloudfront_facts.py and add unit tests (https://github.com/ansible-collections/amazon.aws/pull/1265).
- The ``black`` code formatter has been run across the collection to improve code consistency (https://github.com/ansible-collections/amazon.aws/pull/1465).
- amazon.aws inventory plugins - additional refactorization of inventory plugin connection handling (https://github.com/ansible-collections/amazon.aws/pull/1271).
- amazon.aws lookup plugins - ``aws_access_key`` has been renamed to ``access_key`` for consistency between modules and plugins, ``aws_access_key`` remains as an alias. This change should have no observable effect for users outside the module/plugin documentation (https://github.com/ansible-collections/amazon.aws/pull/1225).
- amazon.aws lookup plugins - ``aws_profile`` has been renamed to ``profile`` for consistency between modules and plugins, ``aws_profile`` remains as an alias. This change should have no observable effect for users outside the module/plugin documentation (https://github.com/ansible-collections/amazon.aws/pull/1225).
- amazon.aws lookup plugins - ``aws_secret_key`` has been renamed to ``secret_key`` for consistency between modules and plugins, ``aws_secret_key`` remains as an alias. This change should have no observable effect for users outside the module/plugin documentation (https://github.com/ansible-collections/amazon.aws/pull/1225).
- amazon.aws lookup plugins - ``aws_security_token`` has been renamed to ``session_token`` for consistency between modules and plugins, ``aws_security_token`` remains as an alias. This change should have no observable effect for users outside the module/plugin documentation (https://github.com/ansible-collections/amazon.aws/pull/1225).
- amazon.aws modules - bulk update of import statements following various refactors (https://github.com/ansible-collections/amazon.aws/pull/1310).
- autoscaling_group - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- aws_account_attribute - the ``aws_account_attribute`` lookup plugin has been refactored to use ``AWSLookupBase`` as its base class (https://github.com/ansible-collections/amazon.aws/pull/1225).
- aws_ec2 inventory - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- aws_secret - the ``aws_secret`` lookup plugin has been refactored to use ``AWSLookupBase`` as its base class (https://github.com/ansible-collections/amazon.aws/pull/1225).
- aws_secret - the ``aws_secret`` lookup plugin has been renamed ``secretsmanager_secret``, ``aws_secret`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/1225).
- aws_ssm - the ``aws_ssm`` lookup plugin has been refactored to use ``AWSLookupBase`` as its base class (https://github.com/ansible-collections/amazon.aws/pull/1225).
- aws_ssm - the ``aws_ssm`` lookup plugin has been renamed ``ssm_parameter``, ``aws_ssm`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/1225).
- backup - Add logic for backup_selection* modules (https://github.com/ansible-collections/amazon.aws/pull/1530).
- bulk migration of ``%`` and ``.format()`` to fstrings (https://github.com/ansible-collections/amazon.aws/pull/1483).
- cloud module_utils - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- cloudtrail_info - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- cloudwatchlogs_log_group - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- docs_fragments - ``amazon.aws.boto3`` fragment now pulls the botocore version requirements from ``module_utils.botocore`` (https://github.com/ansible-collections/amazon.aws/pull/1248).
- docs_fragments - common parameters for modules and plugins have been synchronised and moved to ``amazon.aws.common.modules`` and ``amazon.aws.common.plugins`` (https://github.com/ansible-collections/amazon.aws/pull/1248).
- docs_fragments - region parameters for modules and plugins have been synchronised and moved to ``amazon.aws.region.modules`` and ``amazon.aws.region.plugins`` (https://github.com/ansible-collections/amazon.aws/pull/1248).
- ec2_ami - Extend the unit-test coverage of the module (https://github.com/ansible-collections/amazon.aws/pull/1159).
- ec2_ami - allow ``ImageAvailable`` waiter to retry when the image can't be found (https://github.com/ansible-collections/amazon.aws/pull/1321).
- ec2_ami_info - Add unit-tests coverage (https://github.com/ansible-collections/amazon.aws/pull/1252).
- ec2_eip - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- ec2_eni_info - Add unit-tests coverage (https://github.com/ansible-collections/amazon.aws/pull/1236).
- ec2_instance - avoid changing ``module.params`` (https://github.com/ansible-collections/amazon.aws/pull/1187).
- ec2_instance - updated to avoid manipulating ``module.params`` (https://github.com/ansible-collections/amazon.aws/pull/1337).
- ec2_security_group - added rule options to argument specifications to improve handling of inputs (https://github.com/ansible-collections/amazon.aws/pull/1214).
- ec2_security_group - refacter ``get_target_from_rule()`` (https://github.com/ansible-collections/amazon.aws/pull/1221).
- ec2_security_group - refactor rule expansion and add unit tests (https://github.com/ansible-collections/amazon.aws/pull/1261).
- ec2_snapshot - Reenable the integration tests (https://github.com/ansible-collections/amazon.aws/pull/1235).
- ec2_snapshot_info - Add unit-tests coverage (https://github.com/ansible-collections/amazon.aws/pull/1211).
- ec2_vpc_route_table - add support for Carrier Gateway entry (https://github.com/ansible-collections/amazon.aws/pull/926).
- ec2_vpc_subnet - retry fetching subnet details after creation if the first attempt fails (https://github.com/ansible-collections/amazon.aws/pull/1526).
- inventory aws ec2 - add parameter ``use_ssm_inventory`` allowing to query ssm inventory information for configured EC2 instances and populate hostvars (https://github.com/ansible-collections/amazon.aws/issues/704).
- inventory plugins - refactor cache handling (https://github.com/ansible-collections/amazon.aws/pull/1285).
- inventory plugins - refactor file verification handling (https://github.com/ansible-collections/amazon.aws/pull/1285).
- inventory_aws_ec2 integration tests - replace local module ``test_get_ssm_inventory`` by ``community.aws.ssm_inventory_info`` (https://github.com/ansible-collections/amazon.aws/pull/1416).
- kms_key_info - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- lambda - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- lambda - use common ``get_aws_account_info`` helper rather than reimplementing (https://github.com/ansible-collections/amazon.aws/pull/1181).
- lambda_alias - refactored to avoid passing around the complex ``module`` resource (https://github.com/ansible-collections/amazon.aws/pull/1336).
- lambda_alias - updated to avoid manipulating ``module.params`` (https://github.com/ansible-collections/amazon.aws/pull/1336).
- lambda_execute - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- lambda_info - updated to avoid manipulating ``module.params`` (https://github.com/ansible-collections/amazon.aws/pull/1336).
- lambda_layer_info -  add support for parameter version_number to retrieve detailed information for a specific layer version (https://github.com/ansible-collections/amazon.aws/pull/1293).
- module_utils - move RetryingBotoClientWrapper into module_utils.retries for reuse with other plugin types (https://github.com/ansible-collections/amazon.aws/pull/1230).
- module_utils - move exceptions into dedicated python module (https://github.com/ansible-collections/amazon.aws/pull/1246).
- module_utils - refacter botocore version validation into module_utils.botocore for future reuse (https://github.com/ansible-collections/amazon.aws/pull/1227).
- module_utils.acm - Refactor ACMServiceManager class and add unit tests (https://github.com/ansible-collections/amazon.aws/pull/1273).
- module_utils.botocore - Add Ansible AWS User-Agent identification (https://github.com/ansible-collections/amazon.aws/pull/1306).
- module_utils.botocore - refactorization of ``get_aws_region``, ``get_aws_connection_info`` so that the code can be reused by non-module plugins (https://github.com/ansible-collections/amazon.aws/pull/1231).
- module_utils.policy - minor refacter of code to reduce complexity and improve test coverage (https://github.com/ansible-collections/amazon.aws/pull/1136).
- module_utils.s3 - Refactor get_s3_connection into a module_utils for S3 modules and expand module_utils.s3 unit tests (https://github.com/ansible-collections/amazon.aws/pull/1139).
- module_utils/botocore - added support to ``_boto3_conn`` for passing dictionaries of configuration (https://github.com/ansible-collections/amazon.aws/pull/1307).
- plugin_utils - Added ``AWSConnectionBase`` to support refactoring connection plugins (https://github.com/ansible-collections/amazon.aws/pull/1340).
- rds - AWS is phasing out aurora1. Integration tests use aurora2 (aurora-mysql) by default (https://github.com/ansible-collections/amazon.aws/pull/1233).
- rds_cluster - Split up the functional tests in smaller targets (https://github.com/ansible-collections/amazon.aws/pull/1175).
- rds_cluster_snapshot - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- rds_instance - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- rds_instance_info - Add unit-tests coverage (https://github.com/ansible-collections/amazon.aws/pull/1132).
- rds_instance_snapshot - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- rds_param_group - drop Python2 import fallbacks (https://github.com/ansible-collections/amazon.aws/pull/1513).
- route53_health_check - Drop deprecation warning (https://github.com/ansible-collections/community.aws/pull/1335).
- route53_health_check - minor fix for returning health check info while updating a Route53 health check (https://github.com/ansible-collections/amazon.aws/pull/1200).
- route53_health_check - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- route53_info - drop unused imports (https://github.com/ansible-collections/amazon.aws/pull/1462).
- s3_bucket - add support for S3 dualstack endpoint (https://github.com/ansible-collections/amazon.aws/pull/1305).
- s3_bucket - handle missing read permissions more gracefully when possible (https://github.com/ansible-collections/amazon.aws/pull/1406).
- s3_bucket - refactor S3 connection code (https://github.com/ansible-collections/amazon.aws/pull/1305).
- s3_object - refactor S3 connection code (https://github.com/ansible-collections/amazon.aws/pull/1305).
- s3_object - refactor main to reduce complexity (https://github.com/ansible-collections/amazon.aws/pull/1193).
- s3_object_info - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- s3_object_info - refactor S3 connection code (https://github.com/ansible-collections/amazon.aws/pull/1305).

Breaking Changes / Porting Guide
--------------------------------

- The amazon.aws collection has dropped support for ``botocore<1.25.0`` and ``boto3<1.22.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/1342).
- amazon.aws - compatibility code for Python < 3.6 has been removed (https://github.com/ansible-collections/amazon.aws/pull/1257).
- ec2_eip - the previously deprecated ``instance_id`` alias for the ``device_id`` parameter has been removed. Please use the ``device_id`` parameter name instead (https://github.com/ansible-collections/amazon.aws/issues/1176).
- ec2_instance - the default value for ``instance_type`` has been removed. At least one of ``instance_type`` or ``launch_template`` must be specified when launching new instances (https://github.com/ansible-collections/amazon.aws/pull/1315).
- ec2_vpc_dhcp_options - the ``new_options`` return value has been deprecated after being renamed to ``dhcp_config``.  Please use the ``dhcp_config`` or ``dhcp_options`` return values (https://github.com/ansible-collections/amazon.aws/pull/1327).
- ec2_vpc_endpoint - the ``policy_file`` parameter has been removed.  I(policy) with a file lookup can be used instead (https://github.com/ansible-collections/amazon.aws/issues/1178).
- ec2_vpc_net - the ``classic_link_enabled`` return value has been removed. Support for EC2 Classic networking was dropped by AWS (https://github.com/ansible-collections/amazon.aws/pull/1374).
- ec2_vpc_net_info - the ``classic_link_dns_status`` return value has been removed. Support for EC2 Classic networking was dropped by AWS (https://github.com/ansible-collections/amazon.aws/pull/1374).
- ec2_vpc_net_info - the ``classic_link_enabled`` return value has been removed. Support for EC2 Classic networking was dropped by AWS (https://github.com/ansible-collections/amazon.aws/pull/1374).
- module_utils.cloud - the previously deprecated ``CloudRetry.backoff`` has been removed. Please use ``CloudRetry.exponential_backoff`` or ``CloudRetry.jittered_backoff`` instead (https://github.com/ansible-collections/amazon.aws/issues/1110).

Deprecated Features
-------------------

- amazon.aws collection - due to the AWS SDKs Python support policies (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/) support for Python less than 3.8 by this collection is expected to be removed in a release after 2024-12-01 (https://github.com/ansible-collections/amazon.aws/pull/1342).
- amazon.aws collection - due to the AWS SDKs announcing the end of support for Python less than 3.7 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/) support for Python less than 3.7 by this collection has been deprecated and will be removed in release 7.0.0. (https://github.com/ansible-collections/amazon.aws/pull/1342).
- amazon.aws lookup plugins - the ``boto3_profile`` alias for the ``profile`` option has been deprecated, please use ``profile`` instead (https://github.com/ansible-collections/amazon.aws/pull/1225).
- docs_fragments - ``amazon.aws.aws_credentials`` docs fragment has been deprecated please use ``amazon.aws.common.plugins`` instead (https://github.com/ansible-collections/amazon.aws/pull/1248).
- docs_fragments - ``amazon.aws.aws_region`` docs fragment has been deprecated please use ``amazon.aws.region.plugins`` instead (https://github.com/ansible-collections/amazon.aws/pull/1248).
- docs_fragments - ``amazon.aws.aws`` docs fragment has been deprecated please use ``amazon.aws.common.modules`` instead (https://github.com/ansible-collections/amazon.aws/pull/1248).
- docs_fragments - ``amazon.aws.ec2`` docs fragment has been deprecated please use ``amazon.aws.region.modules`` instead (https://github.com/ansible-collections/amazon.aws/pull/1248).
- module_utils.policy - ``ansible_collections.amazon.aws.module_utils.policy.sort_json_policy_dict`` has been deprecated consider using ``ansible_collections.amazon.aws.module_utils.poilcies.compare_policies`` instead (https://github.com/ansible-collections/amazon.aws/pull/1136).
- s3_object - Support for passing ``dualstack`` and ``endpoint_url`` at the same time has been deprecated, the ``dualstack`` parameter is ignored when ``endpoint_url`` is passed. Support will be removed in a release after 2024-12-01 (https://github.com/ansible-collections/amazon.aws/pull/1305).
- s3_object - Support for passing values of ``overwrite`` other than ``always``, ``never``, ``different`` or last ``last`` has been deprecated.  Boolean values should be replaced by the strings ``always`` or ``never`` Support will be removed in a release after 2024-12-01 (https://github.com/ansible-collections/amazon.aws/pull/1305).
- s3_object_info - Support for passing ``dualstack`` and ``endpoint_url`` at the same time has been deprecated, the ``dualstack`` parameter is ignored when ``endpoint_url`` is passed. Support will be removed in a release after 2024-12-01 (https://github.com/ansible-collections/amazon.aws/pull/1305).

Removed Features (previously deprecated)
----------------------------------------

- ec2_vpc_endpoint_info - support for the ``query`` parameter was removed. The ``amazon.aws.ec2_vpc_endpoint_info`` module now only queries for endpoints. Services can be queried using the ``amazon.aws.ec2_vpc_endpoint_service_info`` module (https://github.com/ansible-collections/amazon.aws/pull/1308).
- s3_object - support for creating and deleting buckets using the ``s3_object`` module has been removed. S3 buckets can be created and deleted using the ``amazon.aws.s3_bucket`` module (https://github.com/ansible-collections/amazon.aws/issues/1112).

Bugfixes
--------

- ec2_security_group - file included unreachable code. Fix now removes unreachable code by removing an inapproproate logic (https://github.com/ansible-collections/amazon.aws/pull/1348).
- ec2_vpc_dhcp_option - retry ``describe_dhcp_options`` after creation when ``InvalidDhcpOptionID.NotFound`` is raised (https://github.com/ansible-collections/amazon.aws/pull/1320).
- lambda_execute - Fix waiter error when function_arn is passed instead of name(https://github.com/ansible-collections/amazon.aws/issues/1268).
- module_utils - fixes ``TypeError: deciding_wrapper() got multiple values for argument 'aws_retry'`` when passing positional arguments to functions wrapped by AnsibleAWSModule.client (https://github.com/ansible-collections/amazon.aws/pull/1230).
- rds_param_group - added a check to fail the task while modifying/updating rds_param_group if trying to change DB parameter group family. (https://github.com/ansible-collections/amazon.aws/pull/1169).
- route53_health_check - Fix ``Name`` tag key removal idempotentcy issue when creating health_check with ``use_unique_names`` and ``tags`` set (https://github.com/ansible-collections/amazon.aws/pull/1253).
- s3_bucket - Handle setting of permissions while acl is disabled.(https://github.com/ansible-collections/amazon.aws/pull/1168).

New Plugins
-----------

Lookup
~~~~~~

- aws_collection_constants - expose various collection related constants

New Modules
-----------

- backup_plan - Manage AWS Backup Plans
- backup_plan_info - Describe AWS Backup Plans
- backup_restore_job_info - List information about backup restore jobs
- backup_selection - Create, delete and modify AWS Backup selection
- backup_selection_info - Describe AWS Backup Selections
- backup_tag - Manage tags on backup plan, backup vault, recovery point
- backup_tag_info - List tags on AWS Backup resources
- backup_vault - Manage AWS Backup Vaults
- backup_vault_info - Describe AWS Backup Vaults

v5.5.3
======

Release Summary
---------------

This release contains a few bugfixes for rds_cluster.

Bugfixes
--------

- rds_cluster - Add ``AllocatedStorage``, ``DBClusterInstanceClass``, ``StorageType``, ``Iops``, and ``EngineMode`` to the list of parameters that can be passed when creating or modifying a Multi-AZ RDS cluster (https://github.com/ansible-collections/amazon.aws/pull/1657).
- rds_cluster - Allow to pass GlobalClusterIdentifier to rds cluster on creation (https://github.com/ansible-collections/amazon.aws/pull/1663).

v5.5.2
======

Bugfixes
--------

- cloudwatchevent_rule - Fixes changed status to report False when no change has been made. The module had incorrectly always reported a change. (https://github.com/ansible-collections/amazon.aws/pull/1589)
- ec2_vpc_nat_gateway - fixes to nat gateway so that when the user creates a private NAT gateway, an Elastic IP address should not be allocated. The module had inncorrectly always allocate elastic IP address when creating private nat gateway (https://github.com/ansible-collections/amazon.aws/pull/1632).
- lambda_execute - Fixes to the stack trace output, where it does not contain spaces between each character. The module had incorrectly always outputted extra spaces between each character. (https://github.com/ansible-collections/amazon.aws/pull/1615)

v5.5.1
======

Release Summary
---------------

This release brings few bugfixes.

Bugfixes
--------

- autoscaling_group - fix ValidationError when describing an autoscaling group that has more than 20 target groups attached to it by breaking the request into chunks (https://github.com/ansible-collections/amazon.aws/pull/1593).
- autoscaling_group_info - fix ValidationError when describing an autoscaling group that has more than 20 target groups attached to it by breaking the request into chunks (https://github.com/ansible-collections/amazon.aws/pull/1593).
- aws_account_attribute - raise correct ``AnsibleLookupError`` rather than ``AnsibleError`` (https://github.com/ansible-collections/amazon.aws/issues/1528).
- aws_secret -  raise correct ``AnsibleLookupError`` rather than ``AnsibleError`` (https://github.com/ansible-collections/amazon.aws/issues/1528).
- aws_service_ip_ranges raise correct ``AnsibleLookupError`` rather than ``AnsibleError`` (https://github.com/ansible-collections/amazon.aws/issues/1528).
- aws_ssm - raise correct ``AnsibleLookupError`` rather than ``AnsibleError`` (https://github.com/ansible-collections/amazon.aws/issues/1528).
- ec2_instance - fix check_mode issue when adding network interfaces (https://github.com/ansible-collections/amazon.aws/issues/1403).
- elb_application_lb - fix missing attributes on creation of ALB. The ``create_or_update_alb()`` was including ALB-specific attributes when updating an existing ALB but not when creating a new ALB (https://github.com/ansible-collections/amazon.aws/issues/1510).

v5.5.0
======

Release Summary
---------------

This release contains a number of bugfixes, new features and new modules.  This is the last planned minor release prior to the release of version 6.0.0.

Minor Changes
-------------

- Add connectivity_type to ec2_vpc_nat_gateway module (https://github.com/ansible-collections/amazon.aws/pull/1267).
- cloudwatch - Add metrics and extended_statistic keys to cloudwatch module (https://github.com/ansible-collections/amazon.aws/pull/1133).
- ec2_ami - add support for BootMode, TpmSupport, UefiData params (https://github.com/ansible-collections/amazon.aws/pull/1037).
- ec2_metadata_facts - added support to query instance tags in metadata (https://github.com/ansible-collections/amazon.aws/pull/1186).
- kms_key - Add multi_region option to create_key (https://github.com/ansible-collections/amazon.aws/pull/1290).
- lambda -  add support for function layers when creating or updating lambda function (https://github.com/ansible-collections/amazon.aws/pull/1118).
- lambda_event -  Added support to set FunctionResponseTypes when creating lambda event source mappings (https://github.com/ansible-collections/amazon.aws/pull/1209).
- module_utils/elbv2 - removed compatibility code for ``botocore < 1.10.30`` (https://github.com/ansible-collections/amazon.aws/pull/1477).
- rds_cluster - New ``engine_mode`` parameter (https://github.com/ansible-collections/amazon.aws/pull/941).
- rds_cluster - add new options (e.g., ``db_cluster_instance_class``, ``allocated_storage``, ``storage_type``, ``iops``) (https://github.com/ansible-collections/amazon.aws/pull/1191).
- rds_cluster - update list of supported engines with ``mysql`` and ``postgres`` (https://github.com/ansible-collections/amazon.aws/pull/1191).
- s3_bucket - ensure ``public_access`` is configured before updating policies (https://github.com/ansible-collections/amazon.aws/pull/1511).

Bugfixes
--------

- cloudwatch_metric_alarm - Don't consider ``StateTransitionedTimestamp`` in change detection. (https://github.com/ansible-collections/amazon.aws/pull/1440).
- ec2_instance - Pick up ``app_callback -> set_password`` rather than ``app_callback -> set_passwd`` (https://github.com/ansible-collections/amazon.aws/issues/1449).
- lambda_info - Do not convert environment variables to snake_case when querying lambda config. (https://github.com/ansible-collections/amazon.aws/pull/1457).
- rds_instance - fix type of ``promotion_tier`` as passed to the APIs (https://github.com/ansible-collections/amazon.aws/pull/1475).

New Modules
-----------

- lambda_layer - Creates an AWS Lambda layer or deletes an AWS Lambda layer version
- lambda_layer_info - List lambda layer or lambda layer versions

v5.4.0
======

Release Summary
---------------

This minor release brings bugfixes and minor new features.

Minor Changes
-------------

- ec2_spot_instance - add parameter ``terminate_instances`` to support terminate instances associated with spot requests. (https://github.com/ansible-collections/amazon.aws/pull/1402).
- route53_health_check -  added support for enabling Latency graphs (MeasureLatency) during creation of a Route53 Health Check. (https://github.com/ansible-collections/amazon.aws/pull/1201).

Bugfixes
--------

- ec2_metadata_facts - fix ``AttributeError`` when running the ec2_metadata_facts module on Python 2 managed nodes (https://github.com/ansible-collections/amazon.aws/issues/1358).
- ec2_vol - handle ec2_vol.tags when the associated instance already exists (https://github.com/ansible-collections/amazon.aws/pull/1071).
- rds_instance - Fixed ``TypeError`` when tagging RDS DB with storage type ``gp3`` (https://github.com/ansible-collections/amazon.aws/pull/1437).
- route53_info - Add new return key ``health_check_observations`` for health check operations (https://github.com/ansible-collections/amazon.aws/pull/1419).
- route53_info - Fixed ``Key Error`` when getting status or failure_reason of a health check (https://github.com/ansible-collections/amazon.aws/pull/1419).

v5.3.0
======

Release Summary
---------------

This release brings some minor changes, bugfixes, and deprecated features.

Minor Changes
-------------

- ec2_instance - more consistently return ``instances`` information (https://github.com/ansible-collections/amazon.aws/pull/964).
- ec2_instance - remove unused import (https://github.com/ansible-collections/amazon.aws/pull/1350).
- ec2_key - Add unit-tests coverage (https://github.com/ansible-collections/amazon.aws/pull/1288).
- ec2_vpc_nat_gateway - ensure allocation_id is defined before potential access (https://github.com/ansible-collections/amazon.aws/pull/1350).
- route53_zone - added support for associating multiple VPCs to route53 hosted zones (https://github.com/ansible-collections/amazon.aws/pull/1300).
- s3_bucket - add option to support creation of buckets with object lock enabled (https://github.com/ansible-collections/amazon.aws/pull/1372).

Deprecated Features
-------------------

- support for passing both profile and security tokens through a mix of environment variables and parameters has been deprecated and support will be removed in release 6.0.0. After release 6.0.0 it will only be possible to pass either a profile or security tokens, regardless of mechanism used to pass them.  To explicitly block a parameter coming from an environment variable pass an empty string as the parameter value.  Support for passing profile and security tokens together was originally deprecated in release 1.2.0, however only partially implemented in release 5.0.0 (https://github.com/ansible-collections/amazon.aws/pull/1355).

Bugfixes
--------

- cloudtrail - support to disabling encryption using ``kms_key_id`` (https://github.com/ansible-collections/amazon.aws/pull/1384).
- ec2_key - fix issue when trying to update existing key pair with the same key material (https://github.com/ansible-collections/amazon.aws/pull/1383).
- module_utils/elbv2 - fix change detection by adding default values for ``Scope`` and ``SessionTimeout`` parameters in ``authenticate-oidc`` rules (https://github.com/ansible-collections/amazon.aws/pull/1270).
- module_utils/elbv2 - respect ``UseExistingClientSecret`` parameter in ``authenticate-oidc`` rules (https://github.com/ansible-collections/amazon.aws/pull/1270).
- revert breaking change introduced in 5.2.0 when passing credentials through a mix of environment variables and parameters (https://github.com/ansible-collections/amazon.aws/issues/1353).
- s3_bucket - empty bucket policy was throwing a JSONDecodeError - deal with it gracefully instead (https://github.com/ansible-collections/amazon.aws/pull/1368)

v5.2.0
======

Release Summary
---------------

A minor release containing bugfixes for the ``ec2_eni_info`` module and the ``aws_rds`` inventory plugin, as well as improvements to the ``rds_instance`` module.

Minor Changes
-------------

- amazon.aws collection - refacterization of code to use argument specification ``fallback`` when falling back to environment variables for security credentials and AWS connection details (https://github.com/ansible-collections/amazon.aws/pull/1174).
- rds_instance - Split up the integration test-suite in a series of smaller tests (https://github.com/ansible-collections/amazon.aws/pull/1185).
- rds_instance - add support for gp3 storage type (https://github.com/ansible-collections/amazon.aws/pull/1266).

Bugfixes
--------

- aws_rds - fixes bug in RDS inventory plugin where config file was ignored (https://github.com/ansible-collections/amazon.aws/issues/1304).
- lambda - fix flaky integration test which assumes there are no other lambdas in the account (https://github.com/ansible-collections/amazon.aws/issues/1277)

v5.1.0
======

Release Summary
---------------

This release brings some minor changes, bugfixes, security fixes and deprecated features.

Minor Changes
-------------

- amazon.aws collection - The ``aws_access_key`` parameter has been renamed to ``access_key``, ``access_key`` was previously an alias for this parameter and ``aws_access_key`` remains as an alias.  This change should have no observable effect for users outside the module/plugin documentation. (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``aws_secret_key`` parameter has been renamed to ``secret_key``, ``secret_key`` was previously an alias for this parameter and ``aws_secret_key`` remains as an alias.  This change should have no observable effect for users outside the module/plugin documentation. (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``security_token`` parameter has been renamed to ``session_token``, ``security_token`` was previously an alias for this parameter and ``security_token`` remains as an alias.  This change should have no observable effect for users outside the module/plugin documentation. (https://github.com/ansible-collections/amazon.aws/pull/1172).
- aws_account_attribute lookup plugin - use ``missing_required_lib`` for more consistent error message when boto3/botocore is not available (https://github.com/ansible-collections/amazon.aws/pull/1152).
- aws_ec2 inventory - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).
- aws_ec2 inventory plugin - use ``missing_required_lib`` for more consistent error message when boto3/botocore is not available (https://github.com/ansible-collections/amazon.aws/pull/1152).
- aws_rds inventory plugin - use ``missing_required_lib`` for more consistent error message when boto3/botocore is not available (https://github.com/ansible-collections/amazon.aws/pull/1152).
- aws_secret lookup plugin - use ``missing_required_lib`` for more consistent error message when boto3/botocore is not available (https://github.com/ansible-collections/amazon.aws/pull/1152).
- aws_ssm lookup plugin - use ``missing_required_lib`` for more consistent error message when boto3/botocore is not available (https://github.com/ansible-collections/amazon.aws/pull/1152).
- ec2_instance - minor fix for launching an instance in specified AZ when ``vpc_subnet_id`` is not provided (https://github.com/ansible-collections/amazon.aws/pull/1150).
- ec2_instance - refacter ``tower_callback`` code to handle parameter validation as part of the argument specification (https://github.com/ansible-collections/amazon.aws/pull/1199).
- ec2_instance - the ``instance_role`` parameter has been renamed to ``iam_instance_profile`` to better reflect what it is, ``instance_role`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/1151).
- ec2_instance - the ``tower_callback`` parameter has been renamed to ``aap_callback``, ``tower_callback`` remains as an alias.  This change should have no observable effect for users outside the module documentation (https://github.com/ansible-collections/amazon.aws/pull/1199).
- s3_object_info - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/1181).

Deprecated Features
-------------------

- amazon.aws collection - Support for the ``EC2_ACCESS_KEY`` environment variable has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``access_key`` parameter or ``AWS_ACCESS_KEY_ID`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - Support for the ``EC2_REGION`` environment variable has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``region`` parameter or ``AWS_REGION`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - Support for the ``EC2_SECRET_KEY`` environment variable has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``secret_key`` parameter or ``AWS_SECRET_ACCESS_KEY`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - Support for the ``EC2_SECURITY_TOKEN`` environment variable has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``session_token`` parameter or ``AWS_SESSION_TOKEN`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - Support for the ``EC2_URL`` and ``S3_URL`` environment variables has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``endpoint_url`` parameter or ``AWS_ENDPOINT_URL`` environment variable instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``access_token`` alias for the ``session_token`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``session_token`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``access_token`` alias for the ``session_token`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``session_token`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``aws_security_token`` alias for the ``session_token`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``session_token`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``ec2_access_key`` alias for the ``access_key`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``access_key`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``ec2_region`` alias for the ``region`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``region`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``ec2_secret_key`` alias for the ``secret_key`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``secret_key`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- amazon.aws collection - The ``security_token`` alias for the ``session_token`` parameter has been deprecated and will be removed in a release after 2024-12-01.  Please use the ``session_token`` name instead (https://github.com/ansible-collections/amazon.aws/pull/1172).
- ec2_security_group - support for passing nested lists to ``cidr_ip`` and ``cidr_ipv6`` has been deprecated. Nested lists can be passed through the ``flatten`` filter instead ``cidr_ip: '{{ my_cidrs | flatten }}'`` (https://github.com/ansible-collections/amazon.aws/pull/1213).
- module_utils.url - ``ansible_collections.amazon.aws.module_utils.urls`` is believed to be unused and has been deprecated and will be removed in release 7.0.0.

Security Fixes
--------------

- ec2_instance - fixes leak of password into logs when using ``tower_callback.windows=True`` and ``tower_callback.set_password`` (https://github.com/ansible-collections/amazon.aws/pull/1199).

Bugfixes
--------

- ec2_instance - fixes ``Invalid type for parameter TagSpecifications, value None`` error when tags aren't specified (https://github.com/ansible-collections/amazon.aws/issues/1148).
- module_utils.transformations - ensure that ``map_complex_type`` still returns transformed items if items exists that are not in the type_map (https://github.com/ansible-collections/amazon.aws/pull/1163).

v5.0.2
======

Bugfixes
--------

- ec2_metadata_facts - fixed ``AttributeError`` (https://github.com/ansible-collections/amazon.aws/issues/1134).

v5.0.1
======

Bugfixes
--------

- ec2_vpc_net_info - fix KeyError (https://github.com/ansible-collections/amazon.aws/pull/1109).
- ec2_vpc_net_info - remove hardcoded ``ClassicLinkEnabled`` parameter when request for ``ClassicLinkDnsSupported`` failed (https://github.com/ansible-collections/amazon.aws/pull/1109).
- s3_object - be more defensive when checking the results of ``s3.get_bucket_ownership_controls`` (https://github.com/ansible-collections/amazon.aws/issues/1115).

v5.0.0
======

Release Summary
---------------

In this release we promoted many community modules to Red Hat supported status. Those modules have been moved from the commuity.aws to amazon.aws collection. This release also brings some new features, bugfixes, breaking changes and deprecated features. The amazon.aws collection has dropped support for ``botocore<1.21.0`` and ``boto3<1.18.0``. Support for ``ansible-core<2.11`` has also been dropped.

Major Changes
-------------

- autoscaling_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.autoscaling_group``.
- autoscaling_group_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.autoscaling_group_info``.
- cloudtrail - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.cloudtrail``.
- cloudwatch_metric_alarm - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.cloudwatch_metric_alarm``.
- cloudwatchevent_rule - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.cloudwatchevent_rule``.
- cloudwatchlogs_log_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.cloudwatchlogs_log_group``.
- cloudwatchlogs_log_group_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.cloudwatchlogs_log_group_info``.
- cloudwatchlogs_log_group_metric_filter - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.cloudwatchlogs_log_group_metric_filter``.
- ec2_eip - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_eip``.
- ec2_eip_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.ec2_eip_info``.
- elb_application_lb - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.elb_application_lb``.
- elb_application_lb_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.elb_application_lb_info``.
- execute_lambda - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.execute_lambda``.
- iam_policy - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_policy``.
- iam_policy_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_policy_info``.
- iam_user - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_user``.
- iam_user_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.iam_user_info``.
- kms_key - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.kms_key``.
- kms_key_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.kms_key_info``.
- lambda - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.lambda``.
- lambda_alias - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.lambda_alias``.
- lambda_event - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.lambda_event``.
- lambda_execute - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.lambda_execute``.
- lambda_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.lambda_info``.
- lambda_policy - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.lambda_policy``.
- rds_cluster - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_cluster``.
- rds_cluster_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_cluster_info``.
- rds_cluster_snapshot - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_cluster_snapshot``.
- rds_instance - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_instance``.
- rds_instance_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_instance_info``.
- rds_instance_snapshot - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_instance_snapshot``.
- rds_option_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_option_group``.
- rds_option_group_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_option_group_info``.
- rds_param_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_param_group``.
- rds_snapshot_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_snapshot_info``.
- rds_subnet_group - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.rds_subnet_group``.
- route53 - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.route53``.
- route53_health_check - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.route53_health_check``.
- route53_info - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.route53_info``.
- route53_zone - The module has been migrated from the ``community.aws`` collection. Playbooks using the Fully Qualified Collection Name for this module should be updated to use ``amazon.aws.route53_zone``.

Minor Changes
-------------

- Ability to record and replay the API interaction of a module for testing purpose. Show case the feature with an example (https://github.com/ansible-collections/amazon.aws/pull/998).
- Remove the empty __init__.py file from the distribution, they were not required anymore (https://github.com/ansible-collections/amazon.aws/pull/1018).
- amazon.aws modules - the ``ec2_url`` parameter has been renamed to ``endpoint_url`` for consistency, ``ec2_url`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/992).
- aws_caller_info - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/968).
- aws_ec2 - introduce the ``allow_duplicated_hosts`` configuration key (https://github.com/ansible-collections/amazon.aws/pull/1026).
- cloudformation - avoid catching ``Exception``, catch more specific errors instead (https://github.com/ansible-collections/amazon.aws/pull/968).
- cloudwatch_metric_alarm_info - Added a new module that describes the cloudwatch metric alarms (https://github.com/ansible-collections/amazon.aws/pull/988).
- ec2_group - The ``ec2_group`` module has been renamed to ``ec2_security_group``, ``ec2_group`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/897).
- ec2_group_info - The ``ec2_group_info`` module has been renamed to ``ec2_security_group_info``, ``ec2_group_info`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/897).
- ec2_instance - Add hibernation_options and volumes->ebs->encrypted keys to support stop-hibernate instance (https://github.com/ansible-collections/amazon.aws/pull/972).
- ec2_instance - expanded the use of the automatic retries to ``InsuffienctInstanceCapacity`` (https://github.com/ansible-collections/amazon.aws/issues/1038).
- ec2_metadata_facts - avoid catching ``Exception``, catch more specific errors instead (https://github.com/ansible-collections/amazon.aws/pull/968).
- ec2_security_group - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/968).
- ec2_vpc_endpoint - avoid catching ``Exception``, catch more specific errors instead (https://github.com/ansible-collections/amazon.aws/pull/968).
- ec2_vpc_nat_gateway - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/968).
- ec2_vpc_net_info - handle classic link check for shared VPCs by throwing a warning instead of an error (https://github.com/ansible-collections/amazon.aws/pull/984).
- module_utils/acm - Move to jittered backoff (https://github.com/ansible-collections/amazon.aws/pull/946).
- module_utils/elbv2 - ensures that ``ip_address_type`` is set on creation rather than re-setting it after creation (https://github.com/ansible-collections/amazon.aws/pull/940).
- module_utils/elbv2 - uses new waiters with retries for temporary failures (https://github.com/ansible-collections/amazon.aws/pull/940).
- module_utils/waf - Move to jittered backoff (https://github.com/ansible-collections/amazon.aws/pull/946).
- module_utils/waiters - Add waiters to manage eks_nodegroup module (https://github.com/ansible-collections/community.aws/pull/1415).
- s3_bucket - ``rgw`` was added as an alias for the ``ceph`` parameter for consistency with the ``s3_object`` module (https://github.com/ansible-collections/amazon.aws/pull/994).
- s3_bucket - the ``s3_url`` parameter was merged into the ``endpoint_url`` parameter, ``s3_url`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/994).
- s3_object - added the ``sig_v4`` paramater, enbling the user to opt in to signature version 4 for download/get operations. (https://github.com/ansible-collections/amazon.aws/pull/1014)
- s3_object - minor linting fixes (https://github.com/ansible-collections/amazon.aws/pull/968).
- s3_object - the ``rgw`` parameter was renamed to ``ceph`` for consistency with the ``s3_bucket`` module, ``rgw`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/994).
- s3_object - the ``s3_url`` parameter was merged into the ``endpoint_url`` parameter, ``s3_url`` remains as an alias (https://github.com/ansible-collections/amazon.aws/pull/994).
- s3_object - updated module to add support for handling file upload to a bucket with ACL disabled (https://github.com/ansible-collections/amazon.aws/pull/921).
- s3_object_info - Added a new module that describes S3 Objects (https://github.com/ansible-collections/amazon.aws/pull/977).

Breaking Changes / Porting Guide
--------------------------------

- amazon.aws collection - Support for ansible-core < 2.11 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1087).
- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.21.0`` and ``boto3<1.18.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/934).
- doc_fragments - remove minimum collection requirements from doc_fragments/aws.py and allow pulling those from doc_fragments/aws_boto3.py instead (https://github.com/ansible-collections/amazon.aws/pull/985).
- ec2_ami - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- ec2_ami - the parameter aliases ``DeviceName``, ``VirtualName`` and ``NoDevice`` were previously deprecated and have been removed, please use ``device_name``, ``virtual_name`` and ``no_device`` instead (https://github.com/ansible-collections/amazon.aws/pull/913).
- ec2_eni_info - the mutual exclusivity of the ``eni_id`` and ``filters`` parameters is now enforced, previously ``filters`` would be ignored if ``eni_id`` was set (https://github.com/ansible-collections/amazon.aws/pull/954).
- ec2_instance - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- ec2_key - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- ec2_vol - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- ec2_vpc_dhcp_option_info - the parameter aliases ``DhcpOptionIds`` and ``DryRun`` were previously deprecated and have been removed, please use ``dhcp_options_ids`` and ``no_device`` instead (https://github.com/ansible-collections/amazon.aws/pull/913).
- ec2_vpc_endpoint - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- ec2_vpc_net - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- ec2_vpc_route_table - the default value for ``purge_tags`` has been changed from ``False`` to ``True`` (https://github.com/ansible-collections/amazon.aws/pull/916).
- s3_bucket - the previously deprecated alias ``S3_URL`` for the ``s3_url`` parameter has been removed.  Playbooks shuold be updated to use ``s3_url`` (https://github.com/ansible-collections/amazon.aws/pull/908).
- s3_object - the previously deprecated alias ``S3_URL`` for the ``s3_url`` parameter has been removed.  Playbooks should be updated to use ``s3_url`` (https://github.com/ansible-collections/amazon.aws/pull/908).

Deprecated Features
-------------------

- amazon.aws collection - due to the AWS SDKs announcing the end of support for Python less than 3.7 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/) support for Python less than 3.7 by this collection has been deprecated and will be removed in a release after 2023-05-31 (https://github.com/ansible-collections/amazon.aws/pull/935).
- inventory/aws_ec2 - the ``include_extra_api_calls`` is now deprecated, its value is silently ignored (https://github.com/ansible-collections/amazon.aws/pull/1097).

Bugfixes
--------

- aws_ec2 - address a regression introduced in 4.1.0 (https://github.com/ansible-collections/amazon.aws/pull/862) that cause the presnse of duplicated hosts in the inventory.
- cloudtrail - Fix key error TagList to TagsList (https://github.com/ansible-collections/amazon.aws/issues/1088).
- ec2_instance - Only show the deprecation warning for the default value of ``instance_type`` when ``count`` or ``exact_count`` are specified (https://github.com//issues/980).
- ec2_metadata_facts - fix ``'NoneType' object is not callable`` exception when using Ansible 2.13+ (https://github.com/ansible-collections/amazon.aws/issues/942).
- module_utils/botocore - fix ``object has no attribute 'fail'`` error in error handling (https://github.com/ansible-collections/amazon.aws/pull/1045).
- module_utils/elbv2 - fixes ``KeyError`` when using ``UseExistingClientSecret`` rather than ``ClientSecret`` (https://github.com/ansible-collections/amazon.aws/pull/940).
- module_utils/elbv2 - improvements to idempotency when comparing listeners (https://github.com/ansible-collections/community.aws/issues/604).
- s3_object - also use ``ignore_nonexistent_bucket`` when listing a bucket (https://github.com/ansible-collections/amazon.aws/issues/966).

New Modules
-----------

- cloudtrail_info - Gather information about trails in AWS Cloud Trail.
- cloudwatch_metric_alarm_info - Gather information about the alarms for the specified metric
- s3_object_info - Gather information about objects in S3

v4.5.0
======

Release Summary
---------------

This release contains a minor bugfix for the ``ec2_vol`` module, some minor work on the ``ec2_key`` module, and various documentation fixes.  This is the last planned release of the 4.x series.

Minor Changes
-------------

- ec2_key - minor refactoring and improved unit-tests coverage (https://github.com/ansible-collections/amazon.aws/pull/1288).

Bugfixes
--------

- ec2_vol - handle ec2_vol.tags when the associated instance already exists (https://github.com/ansible-collections/amazon.aws/pull/1071).

v4.4.0
======

Release Summary
---------------

The amazon.aws 4.4.0 release includes a number of security and minor bug fixes.

Minor Changes
-------------

- ec2_instance - refacter ``tower_callback`` code to handle parameter validation as part of the argument specification (https://github.com/ansible-collections/amazon.aws/pull/1199).
- ec2_instance - the ``tower_callback`` parameter has been renamed to ``aap_callback``, ``tower_callback`` remains as an alias.  This change should have no observable effect for users outside the module documentation (https://github.com/ansible-collections/amazon.aws/pull/1199).

Security Fixes
--------------

- ec2_instance - fixes leak of password into logs when using ``tower_callback.windows=True`` and ``tower_callback.set_password`` (https://github.com/ansible-collections/amazon.aws/pull/1199).

v4.3.0
======

Release Summary
---------------

The amazon.aws 4.3.0 release includes a number of minor bug fixes and improvements.
Following the release of amazon.aws 5.0.0, backports to the 4.x series will be limited to
security issues and bugfixes.

Minor Changes
-------------

- ec2_instance - expanded the use of the automatic retries to ``InsuffienctInstanceCapacity`` (https://github.com/ansible-collections/amazon.aws/issues/1038).

Bugfixes
--------

- ec2_metadata_facts - fix ``'NoneType' object is not callable`` exception when using Ansible 2.13+ (https://github.com/ansible-collections/amazon.aws/issues/942).
- module_utils/cloud - Fix ``ValueError: ansible_collections.amazon.aws.plugins.module_utils.core.__spec__ is None`` error on Ansible 2.9 (https://github.com/ansible-collections/amazon.aws/issues/1083).

v4.2.0
======

Minor Changes
-------------

- ec2_security_group - set type as ``list`` for rules->group_name as it can accept both ``str`` and ``list`` (https://github.com/ansible-collections/amazon.aws/pull/971).
- various modules - linting fixups (https://github.com/ansible-collections/amazon.aws/pull/953).

Deprecated Features
-------------------

- module_utils.cloud - removal of the ``CloudRetry.backoff`` has been delayed until release 6.0.0.  It is recommended to update custom modules to use ``jittered_backoff`` or ``exponential_backoff`` instead (https://github.com/ansible-collections/amazon.aws/pull/951).

v4.1.0
======

Minor Changes
-------------

- ec2_instance - expanded the use of the automatic retries on temporary failures (https://github.com/ansible-collections/amazon.aws/issues/927).
- s3_bucket - updated module to enable support for setting S3 Bucket Keys for SSE-KMS (https://github.com/ansible-collections/amazon.aws/pull/882).

Deprecated Features
-------------------

- amazon.aws collection - due to the AWS SDKs announcing the end of support for Python less than 3.7 (https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/) support for Python less than 3.7 by this collection has been deprecated and will be removed in a release after 2023-05-31 (https://github.com/ansible-collections/amazon.aws/pull/935).

Bugfixes
--------

- aws_ec2 - ensure the correct number of hosts are returned when tags as hostnames are used (https://github.com/ansible-collections/amazon.aws/pull/862).
- elb_application_lb - fix ``KeyError`` when balancing across two Target Groups (https://github.com/ansible-collections/community.aws/issues/1089).
- elb_classic_lb - fix ``'NoneType' object has no attribute`` bug when creating a new ELB in check mode with a health check (https://github.com/ansible-collections/amazon.aws/pull/915).
- elb_classic_lb - fix ``'NoneType' object has no attribute`` bug when creating a new ELB using security group names (https://github.com/ansible-collections/amazon.aws/issues/914).

v4.0.0
======

Major Changes
-------------

- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.20.0`` and ``boto3<1.17.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/574).

Minor Changes
-------------

- aws_s3 - Add ``validate_bucket_name`` option, to control bucket name validation (https://github.com/ansible-collections/amazon.aws/pull/615).
- aws_s3 - The ``aws_s3`` module has been renamed to ``s3_object`` (https://github.com/ansible-collections/amazon.aws/pull/869).
- aws_s3 - ``resource_tags`` has been added as an alias for the ``tags`` parameter (https://github.com/ansible-collections/amazon.aws/pull/845).
- ec2_eni - Change parameter ``device_index`` data type to string when passing to ``describe_network_inter`` api call (https://github.com/ansible-collections/amazon.aws/pull/877).
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
- ec2_instance - raise an error when missing permission to stop instance when ``state`` is set to ``rebooted`` (https://github.com/ansible-collections/amazon.aws/pull/671).
- ec2_vpc_igw - use gateway_id rather than filters to paginate if possible to fix 'NoneType' object is not subscriptable error (https://github.com/ansible-collections/amazon.aws/pull/766).
- ec2_vpc_net - fix a bug where CIDR configuration would be updated in check mode (https://github.com/ansible/ansible/issues/62678).
- ec2_vpc_net - fix a bug where the module would get stuck if DNS options were updated in check mode (https://github.com/ansible/ansible/issues/62677).
- elb_classic_lb - modify the return value of _format_listeners method to resolve a failure creating https listeners (https://github.com/ansible-collections/amazon.aws/pull/860).

v3.5.1
======

Release Summary
---------------

3.5.1 is a security bugfix release.

Minor Changes
-------------

- ec2_instance - refacter ``tower_callback`` code to handle parameter validation as part of the argument specification (https://github.com/ansible-collections/amazon.aws/pull/1199).
- ec2_instance - the ``tower_callback`` parameter has been renamed to ``aap_callback``, ``tower_callback`` remains as an alias.  This change should have no observable effect for users outside the module documentation (https://github.com/ansible-collections/amazon.aws/pull/1199).

Security Fixes
--------------

- ec2_instance - fixes leak of password into logs when using ``tower_callback.windows=True`` and ``tower_callback.set_password`` (https://github.com/ansible-collections/amazon.aws/pull/1199).

v3.5.0
======

Release Summary
---------------

Following the release of amazon.aws 5.0.0, 3.5.0 is a bugfix release and the final planned release for the 3.x series.

Minor Changes
-------------

- ec2_security_group - set type as ``list`` for rules->group_name as it can accept both ``str`` and ``list`` (https://github.com/ansible-collections/amazon.aws/pull/971).

Bugfixes
--------

- ec2_metadata_facts - fix ``'NoneType' object is not callable`` exception when using Ansible 2.13+ (https://github.com/ansible-collections/amazon.aws/issues/942).

v3.4.0
======

Minor Changes
-------------

- ec2_instance - expanded the use of the automatic retries on temporary failures (https://github.com/ansible-collections/amazon.aws/issues/927).

Bugfixes
--------

- elb_application_lb - fix ``KeyError`` when balancing across two Target Groups (https://github.com/ansible-collections/community.aws/issues/1089).
- elb_classic_lb - fix ``'NoneType' object has no attribute`` bug when creating a new ELB in check mode with a health check (https://github.com/ansible-collections/amazon.aws/pull/915).
- elb_classic_lb - fix ``'NoneType' object has no attribute`` bug when creating a new ELB using security group names (https://github.com/ansible-collections/amazon.aws/issues/914).

v3.3.1
======

Release Summary
---------------

Various minor documentation fixes.

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

- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.19.0`` and ``boto3<1.16.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/574).

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

- module_utils - support for the original AWS SDK ``boto`` has been deprecated in favour of the ``boto3``/``botocore`` SDK. All ``boto`` based modules have either been deprecated or migrated to ``botocore``, and the remaining support code in module_utils will be removed in release 4.0.0 of the amazon.aws collection. Any modules outside of the amazon.aws and community.aws collections based on the ``boto`` library will need to be migrated to the ``boto3``/``botocore`` libraries (https://github.com/ansible-collections/amazon.aws/pull/575).

v2.3.0
======

Bugfixes
--------

- aws_account_attribute lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_ec2 inventory plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_rds inventory plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_resource_actions callback plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_secret lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_service_ip_ranges lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- aws_ssm lookup plugin - fix linting errors in documentation data (https://github.com/ansible-collections/amazon.aws/pull/701).
- ec2_instance - ec2_instance module broken in Python 3.8 - dict keys modified during iteration (https://github.com/ansible-collections/amazon.aws/issues/709).
- module.utils.s3 - Update validate_bucket_name minimum length to 3 (https://github.com/ansible-collections/amazon.aws/pull/802).

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
- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.18.0`` and ``boto3<1.15.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/502).
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
- aws_s3 - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- aws_s3 - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- aws_s3 - add ``tags`` and ``purge_tags`` features for an S3 object (https://github.com/ansible-collections/amazon.aws/pull/335)
- aws_s3 - new mode to copy existing on another bucket (https://github.com/ansible-collections/amazon.aws/pull/359).
- aws_secret - added support for gracefully handling deleted secrets (https://github.com/ansible-collections/amazon.aws/pull/455).
- aws_ssm - add ``on_missing`` and ``on_denied`` option (https://github.com/ansible-collections/amazon.aws/pull/370).
- cloudformation - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- cloudformation - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_ami - ensure tags are propagated to the snapshot(s) when creating an AMI (https://github.com/ansible-collections/amazon.aws/pull/437).
- ec2_eni - fix idempotency when ``security_groups`` attribute is specified (https://github.com/ansible-collections/amazon.aws/pull/337).
- ec2_eni - timeout increased when waiting for ENIs to finish detaching (https://github.com/ansible-collections/amazon.aws/pull/501).
- ec2_group - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_group - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_group - use a generator rather than list comprehension (https://github.com/ansible-collections/amazon.aws/pull/465).
- ec2_group - use system ipaddress module, available with Python >= 3.3, instead of vendored copy (https://github.com/ansible-collections/amazon.aws/pull/461).
- ec2_instance - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_instance - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_instance - add ``throughput`` parameter for gp3 volume types (https://github.com/ansible-collections/amazon.aws/pull/433).
- ec2_instance - add support for controlling metadata options (https://github.com/ansible-collections/amazon.aws/pull/414).
- ec2_instance - remove unnecessary raise when exiting with a failure (https://github.com/ansible-collections/amazon.aws/pull/460).
- ec2_instance_info - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_instance_info - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_snapshot - migrated to use the boto3 python library (https://github.com/ansible-collections/amazon.aws/pull/356).
- ec2_spot_instance_info - Added a new module that describes the specified Spot Instance requests (https://github.com/ansible-collections/amazon.aws/pull/487).
- ec2_vol - add parameter ``multi_attach`` to support Multi-Attach on volume creation/update (https://github.com/ansible-collections/amazon.aws/pull/362).
- ec2_vol - relax the boto3/botocore requirements and only require botocore 1.19.27 for modifying the ``throughput`` parameter (https://github.com/ansible-collections/amazon.aws/pull/346).
- ec2_vpc_dhcp_option - Now also returns a boto3-style resource description in the ``dhcp_options`` result key.  This includes any tags for the ``dhcp_options_id`` and has the same format as the current return value of ``ec2_vpc_dhcp_option_info``. (https://github.com/ansible-collections/amazon.aws/pull/252)
- ec2_vpc_dhcp_option_info - Now also returns a user-friendly ``dhcp_config`` key that matches the historical ``new_config`` key from ec2_vpc_dhcp_option, and alleviates the need to use ``items2dict(key_name='key', value_name='values')`` when parsing the output of the module. (https://github.com/ansible-collections/amazon.aws/pull/252)
- ec2_vpc_subnet - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- ec2_vpc_subnet - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- integration tests - remove dependency with collection ``community.general`` (https://github.com/ansible-collections/amazon.aws/pull/361).
- module_utils/waiter - add RDS cluster ``cluster_available`` waiter (https://github.com/ansible-collections/amazon.aws/pull/464).
- module_utils/waiter - add RDS cluster ``cluster_deleted`` waiter (https://github.com/ansible-collections/amazon.aws/pull/464).
- module_utils/waiter - add Route53 ``resource_record_sets_changed`` waiter (https://github.com/ansible-collections/amazon.aws/pull/350).
- s3_bucket - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
- s3_bucket - Tests for compatibility with older versions of the AWS SDKs have been removed (https://github.com/ansible-collections/amazon.aws/pull/442).
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

v1.5.1
======

Minor Changes
-------------

- ec2_instance - remove unnecessary raise when exiting with a failure (https://github.com/ansible-collections/amazon.aws/pull/460).

Bugfixes
--------

- ec2_vol - Fixes ``changed`` status when ``modify_volume`` is used, but no new  disk is being attached.  The module incorrectly reported that no change had  occurred even when disks had been modified (iops, throughput, type, etc.). (https://github.com/ansible-collections/amazon.aws/issues/482).
- ec2_vol - fix iops setting and enforce iops/throughput parameters usage (https://github.com/ansible-collections/amazon.aws/pull/334)

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
- aws_secret - add ``on_missing`` and ``on_denied`` option (https://github.com/ansible-collections/amazon.aws/pull/122).
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

- Add ``aws_security_token``, ``aws_endpoint_url`` and ``endpoint_url`` aliases to improve AWS module parameter naming consistency.
- Add support for ``aws_ca_bundle`` to boto3 based AWS modules
- Add support for configuring boto3 profiles using ``AWS_PROFILE`` and ``AWS_DEFAULT_PROFILE``
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
- ec2_placement_group - make ``name`` a required field.
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
- ec2_asg - Ensure ``wait`` is honored during replace operations
- ec2_launch_template - Update output to include latest_version and default_version, matching the documentation
- ec2_transit_gateway - Use AWSRetry before ClientError is handled when describing transit gateways
- ec2_transit_gateway - fixed issue where auto_attach set to yes was not being honored (https://github.com/ansible/ansible/issues/61907)
- ec2_vol - fix filtering bug
- s3_bucket - Accept XNotImplemented response to support NetApp StorageGRID.
