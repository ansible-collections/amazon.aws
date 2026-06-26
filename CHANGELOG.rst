========================
amazon.aws Release Notes
========================

.. contents:: Topics

v11.4.0
=======

Release Summary
---------------

This release includes significant improvements to the ``aws_ssm`` connection plugin,
particularly for Windows hosts, along with new features for ``route53_zone`` and
``rds_instance``. Documentation examples have been updated to use RFC-compliant
addresses throughout the collection.

Minor Changes
-------------

- aws_ssm - Added O(endpoint_url) option for connecting to alternate AWS endpoints. The alias O(aws_endpoint_url) is also supported (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - Improved code organisation by extracting Windows command execution logic into a dedicated WindowsCommandExecutor class (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - Refactored connection plugin to inherit from AWSConnectionBase for consistent AWS credential handling across plugins (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - Renamed connection plugin options for consistency with other AWS plugins. O(aws_access_key_id) renamed to O(access_key); O(aws_secret_access_key) renamed to O(secret_key); O(aws_session_token) renamed to O(session_token); O(aws_profile) renamed to O(profile). Old names are retained as aliases. Additional aliases O(access_key_id) and O(secret_access_key) were also added (https://github.com/ansible-collections/amazon.aws/pull/2909).
- backup_plan - replace realistic version IDs with example UUID format in documentation (https://github.com/ansible-collections/amazon.aws/pull/3008).
- backup_plan_info - replace realistic version IDs with example UUID format in documentation (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_eip - replace AWS public IPs with RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_eni_info - use RFC 1918 private addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_instance - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_instance_info - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_key_info - replace realistic SSH fingerprint with example value in documentation (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_metadata_facts - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_vpc_dhcp_option - use public DNS servers (8.8.4.4, 8.8.8.8) instead of RFC 5737 addresses for DNS examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_vpc_nat_gateway - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_vpc_nat_gateway_info - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_vpc_vpn - replace realistic pre-shared key with obvious example value in documentation (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_vpc_vpn - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- ec2_vpc_vpn_info - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- rds_instance - Added support for self-managed Active Directory parameters ``domain_fqdn``, ``domain_ou``, ``domain_auth_secret_arn``, and ``domain_dns_ips`` to allow joining RDS instances to a self-managed Active Directory domain (https://github.com/ansible-collections/amazon.aws/pull/2977).
- route53 - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- route53_health_check - use RFC 5737 TEST-NET addresses in documentation examples (https://github.com/ansible-collections/amazon.aws/pull/3008).
- route53_zone - add support for ``wait`` and ``wait_timeout`` parameters to wait for DNSSEC state changes to propagate (https://github.com/ansible-collections/amazon.aws/issues/2981).

Bugfixes
--------

- aws_ssm - Fixed PowerShell command execution timeouts on Windows caused by PTY echo issues. Commands are now uploaded to S3 and executed via a small wrapper to avoid echoing large payloads to stdout (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - Fixed PowerShell stdin handling for modules that require stdin input on Windows hosts (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - Fixed Windows SSM connection failures when transferring files with Unicode characters in filenames or content. The connection plugin now properly handles UTF-8 encoding throughout the S3 upload/download process (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - Fixed stderr message accumulation across multiple command executions. Stderr is now flushed at the start of each command to prevent error messages from previous commands appearing in subsequent command output (https://github.com/ansible-collections/amazon.aws/pull/2909).
- aws_ssm - suppress PowerShell progress output in Windows file transfers to prevent stdout pollution that causes transfer failures (https://github.com/ansible-collections/amazon.aws/pull/3013).

v11.3.0
=======

Release Summary
---------------

This minor release adds new features and improvements to the ``autoscaling_group``, ``elb_application_lb``, ``elb_application_lb_info``, ``elb_classic_lb``, ``event_source_aws_cloudtrail``, ``kms_key``, ``s3_bucket``, ``s3_object_info`` module(s).

Minor Changes
-------------

- Various modules and utilities - migrated from deprecated ``ansible.module_utils._text`` to ``ansible.module_utils.common.text.converters`` (https://github.com/ansible-collections/amazon.aws/pull/2860).
- amazon.aws.cloudformation - Fixed an issue where creating a changeset in check mode would fail if the stack is not in a ready state (e.g., UPDATE_IN_PROGRESS). The module now waits for the stack to be in a ready state (UPDATE_COMPLETE) before creating the changeset (https://github.com/ansible-collections/amazon.aws/pull/1910)
- elb_application_lb_info - Fixed return value documentation to correctly reflect actual types and added missing fields (https://github.com/ansible-collections/amazon.aws/issues/2939).
- extensions/eda/plugins/event_source/aws_sqs_queue.py - Added optional support for feedback so that the event can be removed from the SQS Queue on receipt of acknowledgement from ansible-rulebook.
- module_utils/errors - Add support for f-string style parameter interpolation in error handler descriptions to provide more detailed error messages (https://github.com/ansible-collections/amazon.aws/pull/2944).
- s3_bucket - Added O(account_regional) parameter to support creating buckets in the account-regional namespace. Requires at least botocore version 1.42.67 (https://github.com/ansible-collections/amazon.aws/pull/2960).
- s3_bucket - Added support for managing bucket logging configuration (https://github.com/ansible-collections/amazon.aws/pull/2855).

Bugfixes
--------

- autoscaling_group - Fixed duplicate default_cooldown assignment in properties dict (https://github.com/ansible-collections/amazon.aws/pull/2923).
- elb_application_lb - Listener rules are now returned sorted by priority with the default rule appearing last (https://github.com/ansible-collections/amazon.aws/issues/2939).
- elb_application_lb_info - Listener rules are now returned sorted by priority with the default rule appearing last (https://github.com/ansible-collections/amazon.aws/issues/2939).
- kms_key - Fixed parameter reassignment by using passed alias parameter instead of re-fetching from module params (https://github.com/ansible-collections/amazon.aws/pull/2923).
- module_utils/cloudfront_facts - fix TypeError in CloudFrontFactsServiceManager.describe_cloudfront_property (https://github.com/ansible-collections/community.aws/issues/1915).
- s3_object_info - Fixed duplicate dictionary key assignments when retrieving object facts (https://github.com/ansible-collections/amazon.aws/pull/2923).

v11.2.0
=======

Release Summary
---------------

This release introduces several new features and improvements across the collection. Notable additions include support for the ``volume_initialization_rate`` parameter in ``ec2_vol`` to enable Provisioned Initialization Rate when creating volumes from snapshots, and a new ``protected_from_scale_in`` option in ``autoscaling_group`` to control scale-in protection for instances. Route53 modules have been enhanced with new parameters for latency-based routing, including ``routing_region`` and a temporary ``aws_region`` option to support the transition away from the deprecated ``region`` parameter.
The release also includes security fixes addressing potential ReDoS vulnerabilities in ARN and EC2 security group ID parsing, as well as several internal improvements and refactorings to improve code maintainability, error handling, and testability across modules and plugin utilities.
Several deprecations were introduced in inventory plugins to avoid conflicts with Ansible reserved variable names and modernize configuration options. In addition, the release includes code modernization updates such as replacing deprecated ``datetime.utcnow()`` usage with timezone-aware alternatives, improvements to inventory plugin utilities, and various testing and internal maintenance updates.

Minor Changes
-------------

- autoscaling_group - Added a boolean parameter ``protected_from_scale_in`` to toggle protection from scale-in. This allows users to enable or disable scale-in protection for instances in an autoscaling group. (https://github.com/ansible-collections/amazon.aws/pull/2207)
- aws_cloudtrail - replace deprecated ``datetime.utcnow()`` with timezone-aware ``datetime.now(tz=timezone.utc)`` (https://github.com/ansible-collections/amazon.aws/pull/2858).
- aws_ec2 - added "ec2_tags" host variable (https://github.com/ansible-collections/amazon.aws/pull/2847).
- aws_ec2 - remove explicit ``disable_lookups=False`` parameter from template calls as it is deprecated and False is the default value (https://github.com/ansible-collections/amazon.aws/pull/2864).
- aws_inventory_base - remove explicit ``disable_lookups=False`` parameter from template calls as it is deprecated and False is the default value (https://github.com/ansible-collections/amazon.aws/pull/2864).
- aws_rds - added "rds_tags" host variable (https://github.com/ansible-collections/amazon.aws/pull/2847).
- aws_resource_actions - remove redundant ``list()`` call when using ``sorted()``, improving efficiency by allowing sorted() to consume the generator expression directly (https://github.com/ansible-collections/amazon.aws/pull/2882).
- ec2_vol - added ``volume_initialization_rate`` optional parameter to support Provisioned Initialization Rate when creating a volume from snapshots. (https://github.com/ansible-collections/amazon.aws/issues/2665)
- ec2_vpc_endpoint - replace deprecated ``datetime.utcnow()`` with timezone-aware ``datetime.now(datetime.timezone.utc)`` (https://github.com/ansible-collections/amazon.aws/pull/2866).
- ec2_vpc_nat_gateway - replace deprecated ``datetime.utcnow()`` with timezone-aware ``datetime.now(datetime.timezone.utc)`` (https://github.com/ansible-collections/amazon.aws/pull/2866).
- plugin_utils/inventory - add error handling for ClientError and BotoCoreError in _freeze_iam_role method (https://github.com/ansible-collections/amazon.aws/pull/2902).
- plugin_utils/inventory - extract role session name generation into separate method to improve code organisation (https://github.com/ansible-collections/amazon.aws/pull/2902).
- route53 - added ``routing_region`` parameter to explicitly specify the region for latency-based resource record sets (https://github.com/ansible-collections/amazon.aws/issues/2893).
- route53 - added temporary ``aws_region`` parameter to allow specifying the AWS region for API requests while the ``region`` parameter is being transitioned (https://github.com/ansible-collections/amazon.aws/issues/2893).
- route53 - refactored module utility to use decorator-based error handling. (https://github.com/ansible-collections/amazon.aws/pull/2892)
- route53_health_check - refactored module to improve testability and type safety. (https://github.com/ansible-collections/amazon.aws/pull/2892)

Deprecated Features
-------------------

- aws_ec2 - the ``tags`` host variable has been deprecated to avoid conflicts with Ansible reserved variable names and will be removed in a release after 2026-12-01. Use ``ec2_tags`` instead (https://github.com/ansible-collections/amazon.aws/pull/2847).
- aws_ec2 - the ``use_contrib_script_compatible_ec2_tag_keys`` option has been deprecated and will be removed in a release after 2026-12-01. Use the ``ec2_tags`` structure instead. (https://github.com/ansible-collections/amazon.aws/pull/2854)
- aws_ec2 - the ``use_contrib_script_compatible_sanitization`` option has been deprecated and will be removed in a release after 2026-12-01. Use Ansible's default group name sanitization instead. (https://github.com/ansible-collections/amazon.aws/pull/2854)
- aws_rds - the ``tags`` host variable has been deprecated to avoid conflicts with Ansible reserved variable names and will be removed in a release after 2026-12-01. Use ``rds_tags`` instead (https://github.com/ansible-collections/amazon.aws/pull/2847).
- route53 - the ``region`` parameter for latency-based routing has been deprecated and will be removed in a release after 2027-06-01. The ``routing_region`` parameter behaves exactly as ``region`` behaves today and should be used instead (https://github.com/ansible-collections/amazon.aws/issues/2893).

Security Fixes
--------------

- arn - fix potential ReDoS vulnerability in ARN parsing regex by using negated character class instead of non-greedy quantifier (https://github.com/ansible-collections/amazon.aws/pull/2884).
- ec2_security_group - fix potential ReDoS vulnerability in security group ID parsing regex by using negated character classes and adding end anchor (https://github.com/ansible-collections/amazon.aws/pull/2884).

Bugfixes
--------

- aws_ssm - Fixed connection being re-established on every loop iteration. The plugin now properly establishes a single connection for a loop (https://github.com/ansible-collections/amazon.aws/pull/2869).

v11.1.0
=======

Release Summary
---------------

This release adds support for indirect node counts across various EC2, RDS, and S3 resources. It also introduces the new ``amazon.aws.ec2_instance_type_info`` module to support EC2 instance types. Furthermore, the ``aws_cloudtrail`` and ``aws_sqs_queue`` Event Source plugins have been ported from the  ``ansible.eda`` collection; please note that this introduces ``aiobotocore >= 2.14.0`` as a new dependency for this collection. Several bugfixes are included for the ``elb_application_lb`` and ``s3_object`` modules.

Minor Changes
-------------

- Add the indirect node counts for various EC2 types, RDS types and S3 (https://github.com/ansible-collections/amazon.aws/pull/2743).
- ec2_instance_type_info - new module to return information about EC2 instance types (https://github.com/ansible-collections/amazon.aws/pull/2805).
- extensions/eda/plugins/event_source/aws_cloudtrail - new event source plugin ported from ansible.eda (https://github.com/ansible-collections/amazon.aws/pull/2816).
- extensions/eda/plugins/event_source/aws_sqs_queue - new event source plugin ported from ansible.eda (https://github.com/ansible-collections/amazon.aws/pull/2816).
- requirements.txt - Added ``aiobotocore`` as a dependency for the event source plugins only (https://github.com/ansible-collections/amazon.aws/pull/2816).

Bugfixes
--------

- elb_application_lb - fixed comparison of multi-rule default actions to properly handle the ``Order`` field when determining if listener modifications are needed (https://github.com/ansible-collections/amazon.aws/issues/2537).
- elb_application_lb - fixed error where creating a new application load balancer with listener rules would fail with ``Parameter validation failed: Invalid type for parameter ListenerArn, value: None`` (https://github.com/ansible-collections/amazon.aws/issues/2400).
- s3_object - fixed error when using PUT with an empty ``content`` string (https://github.com/ansible-collections/amazon.aws/pull/2810)

New Modules
-----------

- ec2_instance_type_info - Retrieve information about EC2 instance types

v11.0.0
=======

Release Summary
---------------

This major release includes changes such as refactored S3 module utilities to consolidate duplicate code, add comprehensive type hints and docstrings, and improve maintainability. Additionally, ``botocore`` and ``boto3`` versions have been bumped to 1.35.0 and ``awscli`` version has been bumped to 1.34.0.

Major Changes
-------------

- amazon.aws collection - ``awscli`` version has been bumped to 1.34.0 (https://github.com/ansible-collections/amazon.aws/pull/2774).
- amazon.aws collection - ``botocore`` and ``boto3`` versions have been bumped to 1.35.0 (https://github.com/ansible-collections/amazon.aws/pull/2774).
- ec2_security_group - Support for passing nested lists of strings to ``rules.cidr_ip`` and ``rules.cidr_ipv6`` have been removed (https://github.com/ansible-collections/amazon.aws/issues/2777).
- iam_user - Support for ``iam_user`` return key has been removed; only ``user`` is now returned (https://github.com/ansible-collections/amazon.aws/issues/2777).
- lambda_info - Support for ``function`` has been removed (https://github.com/ansible-collections/amazon.aws/issues/2777).
- route53_info - Support for CamelCased lists (``ResourceRecordSets``, ``HostedZones``, ``HealthChecks``, ``CheckerIpRanges``, ``DelegationSets``, ``HealthCheck``) have been removed (https://github.com/ansible-collections/amazon.aws/issues/2777).
- s3_object - Support for ``list`` mode has been removed; use ``s3_object_info`` instead (https://github.com/ansible-collections/amazon.aws/issues/2777).
- s3_object - Support for passing the leading ``/`` has been removed (https://github.com/ansible-collections/amazon.aws/issues/2777).
- s3_object_info - Support for passing ``dualstack`` and ``endpoint_url`` at the same time has been removed (https://github.com/ansible-collections/amazon.aws/issues/2777).

Minor Changes
-------------

- module_utils/s3 - refactored S3 module utilities to consolidate duplicate code, add comprehensive type hints and docstrings, and improve maintainability (https://github.com/ansible-collections/amazon.aws/pull/2782).
- s3_bucket - refactored to use centralized S3 wrapper functions from module_utils and consistently use S3ErrorHandler (https://github.com/ansible-collections/amazon.aws/pull/2782).
- s3_bucket_info - refactored to use centralized S3 wrapper functions from module_utils and consistently use S3ErrorHandler (https://github.com/ansible-collections/amazon.aws/pull/2782).
- s3_object - refactored to use centralized S3 wrapper functions from module_utils and consistently use S3ErrorHandler (https://github.com/ansible-collections/amazon.aws/pull/2782).
- s3_object_info - refactored to use centralized S3 wrapper functions from module_utils and consistently use S3ErrorHandler (https://github.com/ansible-collections/amazon.aws/pull/2782).

v10.3.2
=======

Bugfixes
--------

- Add retry state for 404 in S3 waiters to avoid failure on s3 bucket 404 if bucket is not immediately visible (https://github.com/ansible-collections/amazon.aws/issues/2984#issuecomment-4603538914) (https://github.com/ansible-collections/amazon.aws/pull/2987)

v10.3.1
=======

Release Summary
---------------

This patch release includes bugfixes for the ``s3_object_info``, ``autoscaling_group``, and ``kms_key`` modules, addressing duplicate dictionary key assignments and improving reliability. It also fixes a TypeError in CloudFront module utilities.

Bugfixes
--------

- autoscaling_group - Fixed duplicate default_cooldown assignment in properties dict (https://github.com/ansible-collections/amazon.aws/pull/2923).
- kms_key - Fixed parameter reassignment by using passed alias parameter instead of re-fetching from module params (https://github.com/ansible-collections/amazon.aws/pull/2923).
- module_utils/cloudfront_facts - fix TypeError in CloudFrontFactsServiceManager.describe_cloudfront_property (https://github.com/ansible-collections/community.aws/issues/1915).
- s3_object_info - Fixed duplicate dictionary key assignments when retrieving object facts (https://github.com/ansible-collections/amazon.aws/pull/2923).

v10.3.0
=======

Release Summary
---------------

This release includes several new features, fixes, and improvements. DNSSEC support has been added to the route53_zone module, allowing users to enable or disable DNSSEC for their hosted zones. The lambda module now supports the new Snapstart configurations for Lambda Functions for improved cold start performance. The ec2_vol module has been enhanced to support specifying an outpost_arn for creating volumes in AWS Outposts.

Minor Changes
-------------

- ec2_vol - Added the ``outpost_arn`` parameter to allow creating volumes in an outpost (https://github.com/ansible-collections/amazon.aws/pull/2695).
- lambda - Added support for SnapStart configuration in Lambda functions, allowing users to configure ``ApplyOn`` with values ``PublishedVersions`` or ``None`` to improve cold start performance for Java-based Lambda functions (https://github.com/ansible-collections/amazon.aws/issues/2727).
- route53_zone - Added DNSSEC support with ``dnssec_enabled`` parameter to enable or disable DNSSEC for private hosted zones (https://github.com/ansible-collections/amazon.aws/pull/2698).
- route53_zone - Added ``dnssec_status`` to module return value showing current DNSSEC status (https://github.com/ansible-collections/amazon.aws/pull/2698).

Bugfixes
--------

- cloudwatchlogs_log_group_info - The documentation has been updated to reflect the fact that log_group_name allows a list of log group names (https://github.com/ansible-collections/amazon.aws/pull/2731).
- ec2_ami_info - fix ``DeprecationTime`` causing a ``KeyError`` as this is not always present in the response (https://github.com/ansible-collections/amazon.aws/issues/2759).
- ec2_security_group_info - ``from_port`` and ``to_port`` values in ``ip_permissions`` are now returned as integers instead of strings for consistency (https://github.com/ansible-collections/amazon.aws/pull/2697).

v10.2.0
=======

Release Summary
---------------

This release includes new features, bug fixes, and enhancements. The elb_classic_lb module now supports specifying internal subnets when the ``scheme`` parameter is set to ``internal``, enabling users to deploy classic load balancers within private subnets for internal-only traffic. The secretsmanager_secret module has been enhanced to return the ``created_date``, ``owning_service``, and ``rotation_lambda_arn`` of a secret. The ec2_ami module now exposes the ``tpm_support`` and ``imds_support`` parameters. The collection has also been updated to remove Python 3.9 support and dropped Python 3.9 related CI code.

Minor Changes
-------------

- ec2_ami - Added ``tpm_support`` parameter to specify support for NitroTPM when registering an AMI (https://github.com/ansible-collections/amazon.aws/issues/2615).
- ec2_ami - Added support for ``imds_support`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2644).
- elb_classic_lb - Added support for specifying internal ``subnets`` when the ``scheme`` parameter is set to ``internal`` (https://github.com/ansible-collections/amazon.aws/pull/2589).
- secretsmanager_secret - Added ``created_date``, ``owning_service`` and ``rotation_lambda_arn`` to the return value of the module (https://github.com/ansible-collections/amazon.aws/pull/2692).

Bugfixes
--------

- ec2_security_group - Fixed a bug in ``_rules_to_delete`` that attempted to access an undefined ``ip_permissions`` variable when ``rules`` or ``rules_egress`` was set to an empty list; renamed the variable to ``rules_egress`` to correctly reference the egress rules retrieved from the security group in AWS (https://github.com/ansible-collections/amazon.aws/issues/2626).
- ec2_vol - Adding the missing ``outpost_arn`` field to the returned data (https://github.com/ansible-collections/amazon.aws/pull/2695).
- module_utils/arn - Fix error handling when an invalid ARN is passed (https://github.com/ansible-collections/amazon.aws/pull/2693).

v10.1.2
=======

Release Summary
---------------

This release includes bug fixes for the ec2_instance module. The ``instance_type`` value returned by the module is now properly read from the instance's metadata rather than from the module input.

Bugfixes
--------

- ec2_instance - The ``instance_type`` value returned by the module is now properly read from the instance's metadata rather than from the module input (https://github.com/ansible-collections/amazon.aws/issues/2647).

v10.1.1
=======

Release Summary
---------------

This release includes bug fixes for the autoscaling_group and backup_selection modules.

Bugfixes
--------

- autoscaling_group - Fixed ``min_size``, ``max_size`` and ``desired_capacity`` so that ``0`` is a valid option (https://github.com/ansible-collections/amazon.aws/issues/2635).
- backup_selection - Fixed bug where the module would report no changes when ``selection_name`` and ``state`` are the only arguments (https://github.com/ansible-collections/amazon.aws/issues/2630).

v10.1.0
=======

Release Summary
---------------

This release introduces several improvements, bugfixes, and deprecation notices, including migrating to ``black`` for code formatting and upgrading minimum Python version to 3.9.

Bugfixes
--------

- autoscaling_group - Removed a potentially stale ASG lifecycle hooks that could prevent groups from transitioning smoothly during updates (https://github.com/ansible-collections/amazon.aws/pull/2543).

v10.0.0
=======

Release Summary
---------------

This major release includes several backward incompatible changes. The minimum supported versions for ``botocore`` and ``boto3`` have been updated to ``1.34.0`` and the minimum supported ``awscli`` has been updated to ``1.32.0``.  Python versions 3.8 and below are no longer supported. The ``ec2_instance_info`` module now returns an empty list instead of failing when an instance is not found.

Major Changes
-------------

- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.34.0`` and ``boto3<1.34.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/2466).
- amazon.aws collection - The amazon.aws collection has dropped support for ``botocore<1.34.0`` and ``boto3<1.34.0``. Most modules will continue to work with older versions of the AWS SDK, however compatibility with older versions of the SDK is not guaranteed and will not be tested. When using older versions of the SDK a warning will be emitted by Ansible (https://github.com/ansible-collections/amazon.aws/pull/2466).
- amazon.aws collection - The amazon.aws collection has now dropped support for and is no longer tested against ``ansible-core<2.15`` (https://github.com/ansible-collections/amazon.aws/pull/2468).

Minor Changes
-------------

- ec2_vpc_subnet - Add retry functionality for ``DetachInternetGateway`` (https://github.com/ansible-collections/amazon.aws/pull/2517).
- module_utils/botocore - When botocore or boto3 are below the minimum version, emit a deprecation warning (https://github.com/ansible-collections/amazon.aws/pull/2466).
- module_utils/iam - ``validate_iam_identifiers`` return ``None`` if the provided value is not a valid Identifier. It returns the formatted identifier otherwise (https://github.com/ansible-collections/amazon.aws/pull/2461).
- rds_instance - Add ``domain_ou`` parameter, and set ``domain_ou`` and ``domain_auth_secret_arn`` as mutually exclusive with ``domain_iam_role_name`` (https://github.com/ansible-collections/amazon.aws/pull/2410).

Breaking Changes / Porting Guide
--------------------------------

- amazon.aws collection - Support for Python versions before 3.9 has been dropped. This includes versions 3.6, 3.7, and 3.8 (https://github.com/ansible-collections/amazon.aws/pull/2464).
- ec2_instance_info - The module now returns an empty list rather than failing when ``instance_ids`` is defined but no matching instances are found (https://github.com/ansible-collections/amazon.aws/pull/2507).

Deprecated Features
-------------------

- ec2_security_group - Support for passing nested lists of strings to ``rules.cidr_ip`` and ``rules.cidr_ipv6`` has been deprecated.  A list of strings should be passed instead (https://github.com/ansible-collections/amazon.aws/pull/2452).
- iam_user - Support for ``iam_user`` return key has been deprecated, in a release after 2026-05-01, the ``user`` return key should be used (https://github.com/ansible-collections/amazon.aws/issues/1841).
- iam_user - ``iam_user`` return key has been deprecated, in a release after 2026-05-01, the ``user`` return key should be used (https://github.com/ansible-collections/amazon.aws/issues/1841).
- lambda_info - Support for returning a single function using the ``function`` return value has been deprecated.  After 2025-01-01 a list of functions will be returned using the ``functions`` return value (https://github.com/ansible-collections/amazon.aws/pull/2477).
- route53_info - Support for using ``CamelCase`` in the ``resource_record_sets`` return value has been deprecated. After 2025-01-01, return values will only use ``snake_case`` (https://github.com/ansible-collections/amazon.aws/pull/2477).
- route53_info - Support for using ``CamelCase`` in the ``hosted_zones`` return value has been deprecated. After 2025-01-01, return values will only use ``snake_case`` (https://github.com/ansible-collections/amazon.aws/pull/2477).
- route53_info - Support for using ``CamelCase`` in return values has been deprecated. After 2025-01-01, return values will only use ``snake_case`` (https://github.com/ansible-collections/amazon.aws/pull/2477).
- s3_object - Support for passing the leading ``/`` has been deprecated.  After 2025-12-01, objects will always be named as passed without any stripping of the leading ``/`` (https://github.com/ansible-collections/amazon.aws/pull/2504).
- s3_object - Support for the ``list`` mode has been deprecated. After 2025-12-01, ``s3_object_info`` should be used to list objects in an S3 bucket (https://github.com/ansible-collections/amazon.aws/pull/2504).
- s3_object_info - Support for passing ``dualstack`` and ``endpoint_url`` at the same time has been deprecated, the ``dualstack`` parameter is ignored when ``endpoint_url`` is set. Support will be removed in a release after 2025-01-01 (https://github.com/ansible-collections/amazon.aws/pull/2469).

Bugfixes
--------

- ec2_vpc_subnet - Fixes ``AssertionError`` caused by paginated response (https://github.com/ansible-collections/amazon.aws/issues/2516).

v9.5.2
=======

Release Summary
---------------

This patch release includes bugfixes for the ``rds_instance``, ``rds_cluster``, and ``ec2_security_group`` modules.

Bugfixes
--------

- rds_cluster - The ``rds_cluster`` module now returns ``db_cluster_resource_id`` and ``db_cluster_instance_class`` (https://github.com/ansible-collections/amazon.aws/issues/2540).
- rds_instance - fix return key ``db_instance_port`` when creating an RDS instance (https://github.com/ansible-collections/amazon.aws/issues/2540).

v9.5.1
=======

Release Summary
---------------

This is a minor release that updates the IAM module for proper error messaging when creating a role with a invalid JSON policy.

Bugfixes
--------

- iam_role - fix error messaging when creating a role with a invalid JSON policy (https://github.com/ansible-collections/amazon.aws/pull/2525).

v9.5.0
=======

Release Summary
---------------

This release contains a minor feature update for the ``rds_instance`` module.

Minor Changes
-------------

- rds_instance - Allow setting ``allocate_storage`` to ``0`` for Aurora engine RDS instances (https://github.com/ansible-collections/amazon.aws/pull/2485).

Bugfixes
--------

- autoscaling_group - Removed a potentially stale ASG lifecycle hooks that could prevent groups from transitioning smoothly during updates (https://github.com/ansible-collections/amazon.aws/pull/2543).
- ec2_security_group_info - ``from_port`` and ``to_port`` values in ``ip_permissions`` are now returned as integers instead of strings for consistency (https://github.com/ansible-collections/amazon.aws/pull/2551).
- rds_instance - fix return key ``db_instance_port`` when creating an RDS instance (https://github.com/ansible-collections/amazon.aws/issues/2540).

v9.4.0
=======

Release Summary
---------------

This release contains a minor feature update for the ``rds_cluster_snapshot`` module.

Minor Changes
-------------

- rds_cluster_snapshot - Allow users to copy ``db_cluster_snapshot`` from one region to another (https://github.com/ansible-collections/amazon.aws/pull/2497).

Bugfixes
--------

- rds_cluster - The ``rds_cluster`` module now returns ``db_cluster_resource_id`` and ``db_cluster_instance_class`` (https://github.com/ansible-collections/amazon.aws/issues/2540).

v9.3.0
=======

Release Summary
---------------

This release contains a minor feature update for the ``elb_classic_lb`` module to accept internal subnets with the internal scheme.

Minor Changes
-------------

- elb_classic_lb - Added support for specifying internal ``subnets`` when the ``scheme`` parameter is set to ``internal`` (https://github.com/ansible-collections/amazon.aws/pull/2589).

Bugfixes
--------

- autoscaling_group - Fixed ``min_size``, ``max_size`` and ``desired_capacity`` so that ``0`` is a valid option (https://github.com/ansible-collections/amazon.aws/issues/2635).

v9.2.0
=======

Release Summary
---------------

This release contains several minor updates for modules including ``ec2_ami``, ``secretsmanager_secret``, ``ec2_vol``, ``rds_instance``, and ``lambda``.

Minor Changes
-------------

- ec2_ami - Added ``tpm_support`` parameter to specify support for NitroTPM when registering an AMI (https://github.com/ansible-collections/amazon.aws/issues/2615).
- ec2_ami - Added support for ``imds_support`` parameter (https://github.com/ansible-collections/amazon.aws/pull/2644).
- ec2_vol - Added the ``outpost_arn`` parameter to allow creating volumes in an outpost (https://github.com/ansible-collections/amazon.aws/pull/2695).
- lambda - Added support for SnapStart configuration in Lambda functions, allowing users to configure ``ApplyOn`` with values ``PublishedVersions`` or ``None`` to improve cold start performance for Java-based Lambda functions (https://github.com/ansible-collections/amazon.aws/issues/2727).
- rds_instance - Add ``domain_ou`` parameter, and set ``domain_ou`` and ``domain_auth_secret_arn`` as mutually exclusive with ``domain_iam_role_name`` (https://github.com/ansible-collections/amazon.aws/pull/2410).
- route53_zone - Added DNSSEC support with ``dnssec_enabled`` parameter to enable or disable DNSSEC for private hosted zones (https://github.com/ansible-collections/amazon.aws/pull/2698).
- route53_zone - Added ``dnssec_status`` to module return value showing current DNSSEC status (https://github.com/ansible-collections/amazon.aws/pull/2698).
- secretsmanager_secret - Added ``created_date``, ``owning_service`` and ``rotation_lambda_arn`` to the return value of the module (https://github.com/ansible-collections/amazon.aws/pull/2692).

Bugfixes
--------

- backup_selection - Fixed bug where the module would report no changes when ``selection_name`` and ``state`` are the only arguments (https://github.com/ansible-collections/amazon.aws/issues/2630).
- cloudwatchlogs_log_group_info - The documentation has been updated to reflect the fact that log_group_name allows a list of log group names (https://github.com/ansible-collections/amazon.aws/pull/2731).
- ec2_ami_info - fix ``DeprecationTime`` causing a ``KeyError`` as this is not always present in the response (https://github.com/ansible-collections/amazon.aws/issues/2759).
- ec2_instance - The ``instance_type`` value returned by the module is now properly read from the instance's metadata rather than from the module input (https://github.com/ansible-collections/amazon.aws/issues/2647).
- ec2_security_group - Fixed a bug in ``_rules_to_delete`` that attempted to access an undefined ``ip_permissions`` variable when ``rules`` or ``rules_egress`` was set to an empty list; renamed the variable to ``rules_egress`` to correctly reference the egress rules retrieved from the security group in AWS (https://github.com/ansible-collections/amazon.aws/issues/2626).
- ec2_vol - Adding the missing ``outpost_arn`` field to the returned data (https://github.com/ansible-collections/amazon.aws/pull/2695).
- module_utils/arn - Fix error handling when an invalid ARN is passed (https://github.com/ansible-collections/amazon.aws/pull/2693).

v9.1.1
=======

Release Summary
---------------

This release contains a minor fix for Python version compatibility.

Bugfixes
--------

- plugins/module_utils/iam - Fix ``type`` builtin shadowing by renaming iam_resource_type (https://github.com/ansible-collections/amazon.aws/pull/2456).
- s3_object - Fix typo in error message (https://github.com/ansible-collections/amazon.aws/pull/2455).

v9.1.0
=======

Release Summary
---------------

This release contains several minor updates, bugfixes, and deprecation notices.

Minor Changes
-------------

- cloudtrail - Add support for ``is_organization_trail`` parameter to enable a trail for all accounts in an organization (https://github.com/ansible-collections/amazon.aws/issues/2295).
- ec2_instance - Add support for ``operator`` parameter in ``volume_tags`` option (https://github.com/ansible-collections/amazon.aws/pull/2390).
- ec2_instance - Add support for ``placement`` parameter to set affinity, availability zone, tenancy, host ID, and group name options (https://github.com/ansible-collections/amazon.aws/pull/2390).
- ec2_instance - Add support for ``volume_tags`` parameter to apply tags to volumes (https://github.com/ansible-collections/amazon.aws/pull/2390).
- ec2_instance - Add support to set ``CapacityReservationId`` using the ``capacity_reservation_specification`` option (https://github.com/ansible-collections/amazon.aws/pull/2390).
- ec2_security_group - Add support for passing nested lists in ``cidr_ip`` and ``cidr_ipv6`` (https://github.com/ansible-collections/amazon.aws/pull/2401).
- iam_access_key - Add support for querying access key last used time (https://github.com/ansible-collections/amazon.aws/pull/2378).
- iam_access_key_info - Add support for querying access key last used time (https://github.com/ansible-collections/amazon.aws/pull/2378).
- iam_role_info - Add ``RoleLastUsed`` to the output returned by the module (https://github.com/ansible-collections/amazon.aws/pull/2392).
- kms_key - Add support for ``GranteePrincipal`` for kms grants (https://github.com/ansible-collections/amazon.aws/pull/2389).
- rds_cluster - Allow ``master_user_secret_kms_key_id`` to be set (https://github.com/ansible-collections/amazon.aws/pull/2405).
- rds_cluster - Allow ``master_user_secret_kms_key_id`` to be set when restoring a cluster from a snapshot (https://github.com/ansible-collections/amazon.aws/pull/2405).
- rds_cluster_snapshot - Allow setting ``master_user_secret_kms_key_id`` when restoring a cluster from a snapshot (https://github.com/ansible-collections/amazon.aws/pull/2405).
- rds_instance - Allow ``master_user_secret_kms_key_id`` to be set (https://github.com/ansible-collections/amazon.aws/pull/2405).
- rds_instance_snapshot - Allow restoring a DB instance from a snapshot with the ``master_user_secret_kms_key_id`` option (https://github.com/ansible-collections/amazon.aws/pull/2405).
- s3_bucket - ``bucket_key_enabled`` and ``encryption_algorithm`` options are now mutually exclusive (https://github.com/ansible-collections/amazon.aws/pull/2403).
- s3_bucket - ``kms_master_key_id`` option may be passed when ``encryption_algorithm`` is ``AES256`` (https://github.com/ansible-collections/amazon.aws/pull/2403).
- s3_bucket - Update default ``encryption_algorithm`` to ``AES256`` as this is now always enforced by AWS (https://github.com/ansible-collections/amazon.aws/issues/2398).

Deprecated Features
-------------------

- ec2_security_group - Support for passing nested lists of strings to ``rules.cidr_ip`` and ``rules.cidr_ipv6`` has been deprecated.  A list of strings should be passed instead (https://github.com/ansible-collections/amazon.aws/pull/2401).

Bugfixes
--------

- ec2_security_group - Fix ``'list' object has no attribute 'startswith'`` error in rules with more than one nested groups (https://github.com/ansible-collections/amazon.aws/pull/2401).
- s3_bucket - Add support for disabling S3 bucket keys on an S3 bucket (https://github.com/ansible-collections/amazon.aws/pull/2403).

v9.0.0
=======

Release Summary
---------------

This major release brings support for a new module (``ses_identity``) and contains breaking changes to the ``ses_identity`` and ``s3_object`` modules. Additionally, several modules have received minor enhancements, including a new parameter for handling cross-account ``delete_before_put`` for the ``lambda`` module and an ``inline_policies`` return value for the ``iam_role_info`` module.

Major Changes
-------------

- s3_object - Allow uploads to S3 buckets to optionally fail when object_lock is set on the bucket (https://github.com/ansible-collections/amazon.aws/pull/2290).
- ses_identity - This module now returns the ``verification_attributes`` resource in snake_case, instead of camelCase (https://github.com/ansible-collections/amazon.aws/pull/2232).

Minor Changes
-------------

- cloudwatch_metric_alarm - Added ``TreatMissingData`` Support. Users can now specify how CloudWatch treats missing data points when evaluating alarms (https://github.com/ansible-collections/amazon.aws/pull/2321).
- cloudwatchlogs_log_group - ``log_group_name`` is now an alias for ``name`` (https://github.com/ansible-collections/amazon.aws/pull/2362).
- iam_group - add ``iam_group.arn`` to return values (https://github.com/ansible-collections/amazon.aws/pull/2227).
- iam_role_info - add inline_policies return value listing names of inline policies attached to a role (https://github.com/ansible-collections/amazon.aws/pull/2377).
- lambda - add new ``delete_before_put`` parameter to handle cross-account updates (https://github.com/ansible-collections/amazon.aws/pull/2314).
- module_utils - add support for STS assume role with web identity token (https://github.com/ansible-collections/amazon.aws/pull/2375).
- s3_bucket - Accept ``encryption_algorithm: disabled`` as a method to explicitly disable encryption (https://github.com/ansible-collections/amazon.aws/issues/2338).
- ses_identity - Added a new module for managing SES identities (https://github.com/ansible-collections/amazon.aws/pull/2232).

Deprecated Features
-------------------

- iam_user - ``iam_user`` return key has been deprecated, in a release after 2026-05-01, the ``user`` return key should be used (https://github.com/ansible-collections/amazon.aws/issues/1841).

Bugfixes
--------

- aws_ssm connection plugin - Fix documentation markup (https://github.com/ansible-collections/amazon.aws/pull/2381).
- cloudformation - Fixed incorrect parameter type for ``stack_set_id`` in documentation (https://github.com/ansible-collections/amazon.aws/pull/2352).
- rds_instance - The ``apply_immediately`` option was being ignored when modifying an RDS instance (https://github.com/ansible-collections/amazon.aws/pull/2355).

New Modules
-----------

- ses_identity - Manage Amazon SES email and domain identities

v8.2.3
=======

Release Summary
---------------

Re-release of v8.2.2 to fix broken Galaxy tarball.

v8.2.2
=======

Release Summary
---------------

This release contains a minor bugfix.

Bugfixes
--------

- ec2_instance - Fix ``Object of type datetime is not JSON serializable`` error on instance creation (https://github.com/ansible-collections/amazon.aws/pull/2327).

v8.2.1
=======

Release Summary
---------------

This release contains several bugfixes for the ``ec2_instance`` module.

Bugfixes
--------

- ec2_instance - Correctly handle ``tags`` and ``instance_tags`` when managing instance state (https://github.com/ansible-collections/amazon.aws/issues/2298).

v8.2.0
=======

Release Summary
---------------

This release contains several minor improvements for modules including ``ec2_ami``, ``rds_cluster_snapshot``, ``cloudformation``, ``s3_object``, ``elb_application_lb_info``, and ``aws_ssm``.

Minor Changes
-------------

- aws_ssm - Added parameter ``ssm_timeout`` for timeout in seconds for the SSM connection to send commands or receive results (https://github.com/ansible-collections/amazon.aws/pull/2268).
- cloudformation - Added support for ``DeletionPolicy``, ``UpdateReplacePolicy`` for ``cloudformation`` module (https://github.com/ansible-collections/amazon.aws/issues/2215).
- ec2_ami - Add ``deprecate_at`` option allowing an AMI to be deprecated when registered (https://github.com/ansible-collections/amazon.aws/pull/2270).
- ec2_ami - Add ``deregister_snapshots`` option to control when snapshots get deregistered (https://github.com/ansible-collections/amazon.aws/pull/2278).
- elb_application_lb_info - add new attributes ``ip_address_type`` (https://github.com/ansible-collections/amazon.aws/pull/2248).
- rds_cluster_snapshot - Remove engine filter when querying db cluster snapshots (https://github.com/ansible-collections/amazon.aws/pull/2261).
- s3_object - Add ``if_match`` / ``if_none_match`` options to PUT/GET operations (https://github.com/ansible-collections/amazon.aws/pull/2281).

v8.1.0
=======

Release Summary
---------------

This release contains several minor improvements for modules including ``cloudformation``, ``ec2_eip``, ``ec2_spot_instance``, ``ec2_vpc_route_table``, ``elb_application_lb``, and ``route53_health_check`` as well as bugfixes for ``s3_bucket`` and ``rds_cluster_snapshot``. This release also introduces the ``amazon.aws.ec2_spot_instance_info`` module to support EC2 spot instance information.

Minor Changes
-------------

- cloudformation - Add new ``stack_set_id`` return value for ``cloudformation`` module (https://github.com/ansible-collections/amazon.aws/pull/2208).
- ec2_eip - Added ``domain`` return value for ``ec2_eip`` module (https://github.com/ansible-collections/amazon.aws/pull/2214).
- ec2_spot_instance - Add support to ``target_capacity`` option for launching Spot Instances with a specific target capacity (https://github.com/ansible-collections/amazon.aws/pull/2190).
- ec2_spot_instance_info - Adds a new module to support EC2 spot instance information (https://github.com/ansible-collections/amazon.aws/pull/2202).
- ec2_vpc_route_table - Add support to ``destination_prefix_list_id`` option for specifying destination prefix list IDs in route table routes (https://github.com/ansible-collections/amazon.aws/pull/2193).
- ec2_vpc_route_table - Added ``destination_prefix_list_id`` return value for ``ec2_vpc_route_table`` module (https://github.com/ansible-collections/amazon.aws/pull/2193).
- elb_application_lb - Added ``security_groups`` return value for ``elb_application_lb`` module (https://github.com/ansible-collections/amazon.aws/pull/2219).
- route53_health_check - Add support to ``routing_control_arn`` option for managing Route 53 Health Checks with associated routing controls (https://github.com/ansible-collections/amazon.aws/pull/2185).

Bugfixes
--------

- rds_cluster_snapshot - Fixes Ansible engine 2.16 error handling in rds_cluster_snapshot (https://github.com/ansible-collections/amazon.aws/pull/2201).
- s3_bucket - Ensure ``bucket_key_enabled`` is properly set to false when disabled (https://github.com/ansible-collections/amazon.aws/pull/2197).

New Modules
-----------

- ec2_spot_instance_info - Retrieves AWS EC2 Spot Instance requests

v8.0.1
=======

Release Summary
---------------

This release contains minor bugfixes.

Bugfixes
--------

- ec2_eni - Fix ``Subnet.availability_zone_id`` return value (https://github.com/ansible-collections/amazon.aws/pull/2181).

v8.0.0
=======

Release Summary
---------------

This major release brings Python 3.6 support to an end. The collection now requires Python 3.7 at minimum, and will now emit a warning when run against Python 3.7. The new ``amazon.aws.elb_network_lb_info`` module has been added. The collection also contains several minor improvements for modules including ``ec2_security_group``, ``ec2_security_group_info`` and ``s3_object``.

Major Changes
-------------

- amazon.aws collection - Support for Python 3.6 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/2171).

Minor Changes
-------------

- ec2_security_group - Added ``ip_permissions`` return value for ``ec2_security_group`` module (https://github.com/ansible-collections/amazon.aws/pull/2173).
- ec2_security_group_info - Added ``ip_permissions`` return value for ``ec2_security_group_info`` module (https://github.com/ansible-collections/amazon.aws/pull/2173).
- ec2_vpc_subnet - Add ``outpost_arn`` parameter, to specify an AWS Outpost (https://github.com/ansible-collections/amazon.aws/issues/2074).
- elb_network_lb_info - Added new module to retrieve information about AWS NLBs (https://github.com/ansible-collections/amazon.aws/pull/2170).
- s3_object - added ``object_owner`` option to set the ACL for the object (https://github.com/ansible-collections/amazon.aws/pull/2156).

Bugfixes
--------

- kms_key - Fixes issue related to ``SupportedKeyUsages`` not being present in the key policy. (https://github.com/ansible-collections/amazon.aws/pull/2161).
- s3_object - fixed idempotent copying objects to buckets with ACL restrictions (https://github.com/ansible-collections/amazon.aws/pull/2156).

New Modules
-----------

- elb_network_lb_info - Gathers information about elastic network load balancers in AWS

v7.6.1
=======

Release Summary
---------------

This release contains bugfix for the ``ec2_eni`` module.

Bugfixes
--------

- ec2_eni - respect ``attached`` argument when creating an ENI (https://github.com/ansible-collections/amazon.aws/pull/2144).

v7.6.0
=======

Release Summary
---------------

This release contains several new features as well as minor bugfixes for the ``ec2_eni`` and ``s3_bucket`` modules. The collection also contains minor updates to the ``backup_plan``, ``cloudwatch_metric_alarm``, ``cloudwatchlogs_log_group_info``, and ``iam_role_info`` modules.

Minor Changes
-------------

- backup_plan - Add support to ``list_of_tags`` and ``not_resources`` option for managing backup plan (https://github.com/ansible-collections/amazon.aws/issues/2049).
- cloudwatch_metric_alarm - add a list of ``alarm_actions``, ``ok_actions`` and ``insufficient_data_actions`` to the return value (https://github.com/ansible-collections/amazon.aws/pull/2084).
- cloudwatchlogs_log_group_info - Add support for log_group_name as list (https://github.com/ansible-collections/amazon.aws/pull/2063).
- iam_role_info - Add ``boundary`` to the return value (https://github.com/ansible-collections/amazon.aws/pull/2097).

Bugfixes
--------

- ec2_eni - fix ``DeleteOnTermination`` fails when it's used while creating an ENI (https://github.com/ansible-collections/amazon.aws/pull/2111).
- s3_bucket - fixed idempotence issue when ACLs were disabled on bucket creation (https://github.com/ansible-collections/amazon.aws/pull/2130).

v7.5.0
=======

Release Summary
---------------

This release contains the new ``rds_cluster_param_group`` and ``rds_cluster_param_group_info`` modules  to manage RDS cluster parameter groups. The collection also contains minor updates including the ability to set the ``BootMode`` on an EC2 AMI, bugfixes and more.

Minor Changes
-------------

- ec2_ami - ``boot_mode`` optional parameter to control the AMI boot mode (https://github.com/ansible-collections/amazon.aws/pull/1936).
- rds_cluster_param_group - Add new module to manage Amazon RDS cluster parameter groups (https://github.com/ansible-collections/amazon.aws/pull/2005).
- rds_cluster_param_group_info - Add new module to retrieve information about RDS cluster parameter groups (https://github.com/ansible-collections/amazon.aws/pull/2005).

Bugfixes
--------

- cloudwatch_metric_alarm - Fixed idempotency when creating cloudwatch metric alarm without dimensions (https://github.com/ansible-collections/amazon.aws/pull/1865).
- rds_cluster_snapshot - Use the client's ``SourceRegion`` if no source region is provided (https://github.com/ansible-collections/amazon.aws/pull/2062).

New Modules
-----------

- rds_cluster_param_group - Manage RDS cluster parameter groups
- rds_cluster_param_group_info - Describes the properties of specific RDS cluster parameter group.

v7.4.0
=======

Release Summary
---------------

This release contains 2 new modules to manage RDS parameter groups (``rds_instance_param_group`` and ``rds_instance_param_group_info``) and one new module to retrieve information about the availability zones (``aws_az_info``). The collection also contains several minor updates including bugfixes, new capabilities for modules, and more.

Minor Changes
-------------

- aws_az_info - Add new module to retrieve information about the availability zones (https://github.com/ansible-collections/amazon.aws/pull/2021).
- ec2_eni - add ``enable_primary_ipv6`` option to allow configuration of primary IPv6 address (https://github.com/ansible-collections/amazon.aws/issues/2020).
- ec2_vpc_endpoint - Add support to ``tags`` and ``purge_tags`` options for updating tags on an existing VPC endpoint (https://github.com/ansible-collections/amazon.aws/pull/2016).
- rds_instance_param_group - Add new module to manage RDS parameter groups (https://github.com/ansible-collections/amazon.aws/pull/2035).
- rds_instance_param_group_info - Add new module to retrieve RDS parameter groups info (https://github.com/ansible-collections/amazon.aws/pull/2035).
- s3_bucket - Add support for S3 Object Lock configuration (https://github.com/ansible-collections/amazon.aws/pull/2003).

Bugfixes
--------

- ec2_vpc_route_table - Fix idempotent issues when updating routes to use VPC Endpoint Gateways (https://github.com/ansible-collections/amazon.aws/issues/1976).
- s3_bucket - Fix ``accelerate_enabled`` parameter not being applied when creating a bucket (https://github.com/ansible-collections/amazon.aws/issues/2037).

New Modules
-----------

- aws_az_info - Gather information about availability zones in AWS
- rds_instance_param_group - manage RDS parameter groups
- rds_instance_param_group_info - describes the properties of specific RDS parameter group.

v7.3.0
=======

Release Summary
---------------

This release contains several minor updates to modules.

Minor Changes
-------------

- cloudwatch_metric_alarm - Optional parameter ``extended_statistics`` now accepts percentile values above 100 (e.g. p99.9) (https://github.com/ansible-collections/amazon.aws/pull/1977).
- ec2_key - Add ``file_name`` option to write the private key to a file on disk (https://github.com/ansible-collections/amazon.aws/pull/1926).
- ec2_key - Add ``source_tags`` and ``tags`` option to import a key pair to AWS (https://github.com/ansible-collections/amazon.aws/pull/1998).
- ec2_launch_template - Add ``cpu_manufacturer`` option to ``instance_requirements`` (https://github.com/ansible-collections/amazon.aws/pull/1990).

Bugfixes
--------

- s3_bucket - fix double redirection issue with S3 bucket regions.

v7.2.0
=======

Release Summary
---------------

This release contains several minor updates to modules.

Minor Changes
-------------

- cloudtrail - Add support for ``advanced_event_selectors``.
- ec2_snapshot - Improvements to automatic retries and snapshot completion polling (https://github.com/ansible-collections/amazon.aws/pull/1933).
- ec2_snapshot_info - Returns data about encryption status, owner_id, and owner_alias (https://github.com/ansible-collections/amazon.aws/pull/1933).
- ec2_vol - Returns data about encryption status, state, and throughput (https://github.com/ansible-collections/amazon.aws/pull/1933).
- ec2_vol_info - Returns data about encryption status, kms_key_id, state, and throughput (https://github.com/ansible-collections/amazon.aws/pull/1933).
- iam_role - Add support for ``path`` option (https://github.com/ansible-collections/amazon.aws/pull/1931).
- kms_key - Add support for ``primary_key`` option and related return value (https://github.com/ansible-collections/amazon.aws/pull/1936).
- rds_cluster - Add ``db_cluster_instance_class`` option for Multi-AZ DB clusters (https://github.com/ansible-collections/amazon.aws/pull/1936).
- rds_instance - Add ``db_cluster_identifier`` option for multi-AZ DB clusters (https://github.com/ansible-collections/amazon.aws/pull/1936).
- rds_instance - Add ``storage_throughput`` option for configuring gp3 storage (https://github.com/ansible-collections/amazon.aws/pull/1936).
- s3_bucket - Add ``transfer_acceleration`` and ``public_access`` options for S3 bucket (https://github.com/ansible-collections/amazon.aws/pull/1896).
- s3_bucket - Add ``website`` and ``delete_object_ownership`` options for S3 bucket (https://github.com/ansible-collections/amazon.aws/pull/1926).

v7.1.0
=======

Release Summary
---------------

This release contains several minor bugfixes and new features.

Minor Changes
-------------

- elb_classic_lb - Add support for ``connection_draining_timeout`` parameter (https://github.com/ansible-collections/amazon.aws/pull/1895).
- kms_key - Add ``origin`` parameter for specifying origin of KMS key (https://github.com/ansible-collections/amazon.aws/pull/1888).
- kms_key - Add ``state: absent`` support for deleting imported KMS keys (https://github.com/ansible-collections/amazon.aws/pull/1888).
- module_utils.rds - Refactored ``ensure_present`` function to fix PEP8 N802 naming convention (https://github.com/ansible-collections/amazon.aws/pull/1885).
- rds_cluster - Add support for ``replication_source_identifier`` and ``source_region`` parameters to enable cross-region replication (https://github.com/ansible-collections/amazon.aws/pull/1886).
- s3_bucket - Add support for ``delete_contents`` parameter (https://github.com/ansible-collections/amazon.aws/pull/1874).
- s3_bucket - Add support for ``expected_bucket_owner`` parameter (https://github.com/ansible-collections/amazon.aws/pull/1907).

Bugfixes
--------

- kms_key - Fix ``key_spec`` parameter for imported key material (https://github.com/ansible-collections/amazon.aws/pull/1888).
- kms_key_info - Fix ``multi_region_configuration`` return value (https://github.com/ansible-collections/amazon.aws/pull/1888).
- module_utils.elbv2 - Fixes error handling when rules have no condition (https://github.com/ansible-collections/amazon.aws/pull/1867).
- module_utils.elbv2 - Fixes error handling when rules have multiple path conditions (https://github.com/ansible-collections/amazon.aws/pull/1867).

v7.0.0
=======

Release Summary
---------------

This major release brings an end to support for Ansible version 2.12 and 2.13 and Python version 3.6. The collection now requires ``ansible-core>=2.14`` and ``python>=3.7`` at minimum. Additionally, support for ``botocore>=1.25.0`` and ``boto3>=1.22.0`` has been added.

Major Changes
-------------

- amazon.aws collection - Support for ``botocore<1.25.0`` and ``boto3<1.22.0`` has been dropped. (https://github.com/ansible-collections/amazon.aws/pull/1832).
- amazon.aws collection - Support for ansible-core < 2.14 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1831).
- amazon.aws collection - Support for python<3.7 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1832).

Minor Changes
-------------

- cloudwatchlogs_log_group - add support for ``kms_key_id`` option for encrypting log data (https://github.com/ansible-collections/amazon.aws/pull/1822).
- cloudwatchlogs_log_group - add support for ``skip_destroy`` option to prevent log group deletion (https://github.com/ansible-collections/amazon.aws/pull/1822).
- cloudwatchlogs_log_group_metric_filter - Add support for ``unit`` option (https://github.com/ansible-collections/amazon.aws/pull/1813).
- ec2_instance - add support for ``sriov_net_support`` option (https://github.com/ansible-collections/amazon.aws/pull/1819).
- ec2_instance - add support for ``volume_initialization_rate_iops`` option (https://github.com/ansible-collections/amazon.aws/pull/1836).
- ec2_launch_template - Add support for ``network_interfaces`` option (https://github.com/ansible-collections/amazon.aws/pull/1848).
- elb_application_lb - Add support for ``mutual_authentication`` option (https://github.com/ansible-collections/amazon.aws/pull/1824).
- elb_application_lb_info - Add support for ``mutual_authentication`` return key (https://github.com/ansible-collections/amazon.aws/pull/1824).

v6.5.0
=======

Release Summary
---------------

This release contains several minor bugfixes and new features.

Minor Changes
-------------

- cloudwatchlogs_log_group_info - Refactored log group info implementation, no longer calling ``describe_subscription_filters()`` by default (https://github.com/ansible-collections/amazon.aws/pull/1773).
- ec2_eni_info - Add ``include_attached_instance`` option to include attached instance information (https://github.com/ansible-collections/amazon.aws/pull/1754).
- ec2_eni_info - Renamed ``attached`` to ``attachment`` for consistency in return value documentation (https://github.com/ansible-collections/amazon.aws/pull/1754).
- ec2_instance - Add ``auto_recovery`` option to enable instance auto-recovery (https://github.com/ansible-collections/amazon.aws/pull/1755).
- ec2_metadata_facts - Add ``hostname`` and ``hostname_fqdn`` to return facts (https://github.com/ansible-collections/amazon.aws/pull/1777).
- ec2_security_group - Add ``multi_account`` option for specifying external AWS account source IDs in security groups (https://github.com/ansible-collections/amazon.aws/pull/1792).
- rds_instance - Added ``preferred_backup_window`` option for modifying existing instances (https://github.com/ansible-collections/amazon.aws/pull/1764).
- s3_object - Adds an ``overwrite`` option to control overwriting objects (https://github.com/ansible-collections/amazon.aws/pull/1780).

Bugfixes
--------

- ec2_instance - Fixes issue with ``terminated`` state where user_data was improperly being passed to the API call (https://github.com/ansible-collections/amazon.aws/issues/1740).
- rds_instance - Improve handling of ``DbiResourceId`` key in instance info (https://github.com/ansible-collections/amazon.aws/pull/1764).

v6.4.0
=======

Release Summary
---------------

This release contains several minor bugfixes and new features.

Minor Changes
-------------

- cloudtrail - Add support for ``network_activity_events`` option (https://github.com/ansible-collections/amazon.aws/pull/1693).
- cloudwatch_metric_alarm - Add support for ``threshold_metric_id`` option (https://github.com/ansible-collections/amazon.aws/pull/1715).
- ec2_instance - Add support for additional ENI subnet and security group options (https://github.com/ansible-collections/amazon.aws/pull/1708).
- ec2_instance - Add support for ``associate_public_ip_address`` option (https://github.com/ansible-collections/amazon.aws/pull/1731).
- elb_application_lb - Add support for ``ip_address_type`` option (https://github.com/ansible-collections/amazon.aws/pull/1728).
- rds_cluster - Add support for ``manage_master_user_password`` option (https://github.com/ansible-collections/amazon.aws/pull/1720).
- rds_instance - Add support for ``manage_master_user_password`` option (https://github.com/ansible-collections/amazon.aws/pull/1720).
- route53 - Add support for ``geoproximity_routing`` option (https://github.com/ansible-collections/amazon.aws/pull/1738).
- s3_bucket - Add ``object_lock_enabled`` parameter option (https://github.com/ansible-collections/amazon.aws/pull/1668).

Bugfixes
--------

- ec2_vpc_endpoint - Fix endpoint deletion when endpoint type is ``Gateway`` (https://github.com/ansible-collections/amazon.aws/issues/1650).
- elb_application_lb - Fix application load balancer idempotence when multiple subnets are in the same zone (https://github.com/ansible-collections/amazon.aws/pull/1725).

v6.3.0
=======

Release Summary
---------------

This release contains several minor bugfixes and new features.

Minor Changes
-------------

- cloudtrail - Add support for ``enable_log_file_validation`` option for enabling log file integrity validation (https://github.com/ansible-collections/amazon.aws/pull/1651).
- ec2_instance - Add support for ``instance_initiated_shutdown_behavior`` option for setting shutdown action behavior (https://github.com/ansible-collections/amazon.aws/pull/1647).
- ec2_instance - Add support for ``maintenance_options`` option for configuring instance metadata (https://github.com/ansible-collections/amazon.aws/pull/1647).
- ec2_instance - Add support for ``wait_timeout`` option (https://github.com/ansible-collections/amazon.aws/pull/1666).
- elb_application_lb - Add support for ``connection_logs`` option (https://github.com/ansible-collections/amazon.aws/pull/1673).
- elb_application_lb_info - Add support for ``connection_logs`` return key (https://github.com/ansible-collections/amazon.aws/pull/1673).
- kms_key - Add support for ``primary_key_arn`` option (https://github.com/ansible-collections/amazon.aws/pull/1669).
- rds_instance - Add support for ``dedicated_log_volume`` and ``storage_throughput`` options (https://github.com/ansible-collections/amazon.aws/pull/1665).
- route53_zone - Add ``vpc`` return information (https://github.com/ansible-collections/amazon.aws/pull/1634).

Bugfixes
--------

- ec2_vol_info - Fix idempotency issue when updating tags (https://github.com/ansible-collections/amazon.aws/pull/1644).
- route53_zone - Fix validation of ``delegation_set_id`` option (https://github.com/ansible-collections/amazon.aws/pull/1634).
- s3_object - Fix error handling when source does not exist (https://github.com/ansible-collections/amazon.aws/pull/1627).

v6.2.0
=======

Release Summary
---------------

This release contains several minor bugfixes and new features.

Minor Changes
-------------

- autoscaling_group - Add support for ``capacity_rebalance``, ``default_instance_warmup`` and ``desired_capacity_type`` options (https://github.com/ansible-collections/amazon.aws/pull/1545).
- cloudwatch_metric_alarm - Add support for ``metrics`` option (https://github.com/ansible-collections/amazon.aws/pull/1580).
- ec2_instance - Add support for ``network_interfaces`` option (https://github.com/ansible-collections/amazon.aws/pull/1611).
- ec2_launch_template - Add support for ``disable_api_stop`` and ``enclave_options`` options (https://github.com/ansible-collections/amazon.aws/pull/1591).
- ec2_vpc_endpoint - Add support for ``dns_options`` option (https://github.com/ansible-collections/amazon.aws/pull/1595).
- elb_application_lb - Add ``ip_address_type`` to listener return value (https://github.com/ansible-collections/amazon.aws/pull/1589).
- elb_application_lb - Add support for ``xff_header_processing_mode`` option (https://github.com/ansible-collections/amazon.aws/pull/1602).
- rds_cluster - Add ``allocated_storage`` to return value (https://github.com/ansible-collections/amazon.aws/pull/1614).
- rds_cluster - Add support for ``allocated_storage`` option (https://github.com/ansible-collections/amazon.aws/pull/1614).

Bugfixes
--------

- cloudwatchlogs_log_group - Fix bug when deleting log group with ``absent`` state (https://github.com/ansible-collections/amazon.aws/pull/1569).
- s3_bucket - Fix ``ObjectOwnership`` validation issue (https://github.com/ansible-collections/amazon.aws/issues/1573).
- s3_bucket - Fix ``versioning`` parameter incorrectly being ignored (https://github.com/ansible-collections/amazon.aws/pull/1604).

v6.1.0
=======

Release Summary
---------------

This release contains several minor bugfixes and new features including new modules for managing RDS clusters, RDS cluster snapshots, and RDS option groups.

Minor Changes
-------------

- cloudwatch_metric_alarm - Add support for ``evaluation_periods`` option (https://github.com/ansible-collections/amazon.aws/pull/1534).
- ec2_instance - Add support for ``license_specifications`` option (https://github.com/ansible-collections/amazon.aws/pull/1529).
- ec2_snapshot - Add support for ``snapshot_tags`` option (https://github.com/ansible-collections/amazon.aws/pull/1523).
- elb_application_lb - Add support for ``desync_mitigation_mode`` option (https://github.com/ansible-collections/amazon.aws/pull/1521).
- rds_cluster - New module for managing Amazon RDS clusters (https://github.com/ansible-collections/amazon.aws/pull/1506).
- rds_cluster_snapshot - New module for managing Amazon RDS cluster snapshots (https://github.com/ansible-collections/amazon.aws/pull/1506).
- rds_option_group - New module for managing RDS option groups (https://github.com/ansible-collections/amazon.aws/pull/1506).

Bugfixes
--------

- elb_application_lb - Fix idempotency with multiple listeners (https://github.com/ansible-collections/amazon.aws/issues/1519).
- rds_instance - Fix bug where options were not correctly being modified (https://github.com/ansible-collections/amazon.aws/issues/1517).

New Modules
-----------

- rds_cluster - Manage Amazon RDS clusters
- rds_cluster_snapshot - Manage Amazon RDS cluster snapshots
- rds_option_group - Manage RDS option groups

v6.0.1
=======

Release Summary
---------------

This release contains minor bugfixes.

Bugfixes
--------

- iam_role - Fix ``assume_role_policy_document`` validation (https://github.com/ansible-collections/amazon.aws/pull/1501).
- s3_bucket - Fix updating of bucket ACLs (https://github.com/ansible-collections/amazon.aws/issues/1485).

v6.0.0
=======

Release Summary
---------------

This is the first major release for the ``amazon.aws`` collection version 6.0.0. This release drops support for ``ansible-core<2.12`` and Python versions before 3.6.

Major Changes
-------------

- amazon.aws collection - Support for ansible-core < 2.12 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1440).

Minor Changes
-------------

- amazon.aws modules - Default to ``botocore>=1.25.0`` (https://github.com/ansible-collections/amazon.aws/pull/1432).
- autoscaling_group - Add support for ``predicted_capacity`` option (https://github.com/ansible-collections/amazon.aws/pull/1417).
- cloudwatch_metric_alarm - Add support for ``OK`` and ``ALARM`` states (https://github.com/ansible-collections/amazon.aws/pull/1459).
- ec2_instance - Add support for ``host_resource_group_arn`` option (https://github.com/ansible-collections/amazon.aws/pull/1430).
- ec2_vol - Add support for ``final_snapshot`` option (https://github.com/ansible-collections/amazon.aws/pull/1441).
- iam_managed_policy - Add support for ``description`` option (https://github.com/ansible-collections/amazon.aws/pull/1425).
- rds_instance - Add ``allocate_storage`` return value (https://github.com/ansible-collections/amazon.aws/pull/1451).
- rds_instance - Add support for ``allocate_storage`` option (https://github.com/ansible-collections/amazon.aws/pull/1451).
- rds_instance - Add support for ``network_types`` option (https://github.com/ansible-collections/amazon.aws/pull/1451).
- rds_instance - Add support for ``storage_type`` option (https://github.com/ansible-collections/amazon.aws/pull/1451).
- s3_bucket - Add support for ``object_lock_default_retention`` option (https://github.com/ansible-collections/amazon.aws/pull/1428).

Bugfixes
--------

- cloudwatch_metric_alarm - Fix idempotency when updating dimensions (https://github.com/ansible-collections/amazon.aws/issues/1453).
- ec2_launch_template - Fix issue with ``instance_market_options`` parameter (https://github.com/ansible-collections/amazon.aws/pull/1448).
- elb_application_lb - Fix listener rules processing when creating or updating rules (https://github.com/ansible-collections/amazon.aws/issues/1412).
- route53 - Fix idempotency issue when changing record types (https://github.com/ansible-collections/amazon.aws/pull/1443).

v5.5.3
=======

Release Summary
---------------

This release contains minor bug fixes.

Bugfixes
--------

- ec2_key - Fix bug where keys were not being properly saved when ``key_material`` was provided (https://github.com/ansible-collections/amazon.aws/pull/1408).
- iam_role - Fix idempotency when ``max_session_duration`` is changed (https://github.com/ansible-collections/amazon.aws/pull/1403).

v5.5.2
=======

Release Summary
---------------

This release contains minor bug fixes.

Bugfixes
--------

- cloudwatch_metric_alarm - Fix idempotency when updating alarm configuration (https://github.com/ansible-collections/amazon.aws/issues/1389).
- iam_role - Fix ``permission_boundary`` being incorrectly applied (https://github.com/ansible-collections/amazon.aws/pull/1396).
- rds_instance - Fix ``apply_immediately`` option not being applied to all modifications (https://github.com/ansible-collections/amazon.aws/pull/1393).

v5.5.1
=======

Release Summary
---------------

This release contains minor bug fixes.

Bugfixes
--------

- ec2_instance - Fix idempotency issue with ``network_interfaces`` option (https://github.com/ansible-collections/amazon.aws/pull/1371).
- elb_application_lb - Fixed idempotency issue when updating listeners (https://github.com/ansible-collections/amazon.aws/issues/1366).

v5.5.0
=======

Release Summary
---------------

This release contains several minor features and bugfixes.

Minor Changes
-------------

- backup_plan_info - Added a new module to retrieve information about AWS Backup plans (https://github.com/ansible-collections/amazon.aws/pull/1344).
- backup_selection - Add support for ``not_resources`` option (https://github.com/ansible-collections/amazon.aws/pull/1337).
- backup_selection_info - Added a new module to retrieve information about AWS Backup selections (https://github.com/ansible-collections/amazon.aws/pull/1344).
- backup_vault_info - Added a new module to retrieve information about AWS Backup vaults (https://github.com/ansible-collections/amazon.aws/pull/1344).
- ec2_instance - Add support for ``hibernation_options`` option (https://github.com/ansible-collections/amazon.aws/pull/1343).
- ec2_instance - Add support for ``metadata_options`` option (https://github.com/ansible-collections/amazon.aws/pull/1346).
- ec2_launch_template - Add support for ``cpu_options`` option (https://github.com/ansible-collections/amazon.aws/pull/1351).
- ec2_vol - Add support for ``create_encrypted`` option (https://github.com/ansible-collections/amazon.aws/pull/1358).
- rds_instance - Add support for ``monitoring_interval`` option (https://github.com/ansible-collections/amazon.aws/pull/1330).

Bugfixes
--------

- cloudwatch_metric_alarm - Fixed check mode behavior (https://github.com/ansible-collections/amazon.aws/pull/1323).
- ec2_security_group - Fix idempotency when updating security group rules (https://github.com/ansible-collections/amazon.aws/pull/1318).
- elb_application_lb - Fix idempotency issue with target groups (https://github.com/ansible-collections/amazon.aws/pull/1347).

New Modules
-----------

- backup_plan_info - Retrieves information about AWS Backup plans
- backup_selection_info - Retrieves information about AWS Backup selections
- backup_vault_info - Retrieves information about AWS Backup vaults

v5.4.0
=======

Release Summary
---------------

This release contains several minor features.

Minor Changes
-------------

- ec2_eni - Add support for ``device_index`` option (https://github.com/ansible-collections/amazon.aws/pull/1290).
- ec2_instance - Add support for ``capacity_reservation_specification`` option (https://github.com/ansible-collections/amazon.aws/pull/1289).
- ec2_key - Add ``type`` parameter for RSA or ED25519 key types (https://github.com/ansible-collections/amazon.aws/pull/1291).
- ec2_launch_template - Add support for ``tag_specifications`` option (https://github.com/ansible-collections/amazon.aws/pull/1295).
- elb_application_lb - Add support for ``drop_invalid_header_fields`` option (https://github.com/ansible-collections/amazon.aws/pull/1301).
- elb_application_lb_info - Add support for ``drop_invalid_header_fields`` in return value (https://github.com/ansible-collections/amazon.aws/pull/1301).
- iam_role - Add support for ``permissions_boundary`` option (https://github.com/ansible-collections/amazon.aws/pull/1299).
- kms_key - Add support for ``enable_key_rotation`` and ``rotation_period_in_days`` options (https://github.com/ansible-collections/amazon.aws/pull/1303).
- rds_instance - Add support for ``enable_performance_insights`` option (https://github.com/ansible-collections/amazon.aws/pull/1279).

Bugfixes
--------

- cloudwatchlogs_log_group - Fixed retention_in_days parameter (https://github.com/ansible-collections/amazon.aws/pull/1276).
- ec2_vol - Fix idempotency issue when modifying volume type (https://github.com/ansible-collections/amazon.aws/pull/1287).

v5.3.0
=======

Release Summary
---------------

This release contains several minor features and bugfixes.

Minor Changes
-------------

- ec2_eip - Add support for ``public_ipv4_pool`` option (https://github.com/ansible-collections/amazon.aws/pull/1237).
- ec2_instance - Add support for ``user_data_base64`` option (https://github.com/ansible-collections/amazon.aws/pull/1243).
- ec2_launch_template - Add support for ``instance_requirements`` option (https://github.com/ansible-collections/amazon.aws/pull/1250).
- ec2_vpc_dhcp_option - Add support for ``netbios_node_type`` option (https://github.com/ansible-collections/amazon.aws/pull/1228).
- elb_application_lb - Add support for ``http2`` option (https://github.com/ansible-collections/amazon.aws/pull/1255).
- iam_managed_policy - Add support for ``policy_id`` return value (https://github.com/ansible-collections/amazon.aws/pull/1234).
- kms_key - Add ``enable_rotation`` return value (https://github.com/ansible-collections/amazon.aws/pull/1247).
- s3_bucket - Add support for ``object_ownership`` option (https://github.com/ansible-collections/amazon.aws/pull/1232).

Bugfixes
--------

- ec2_snapshot_info - Fix pagination when filtering snapshots (https://github.com/ansible-collections/amazon.aws/pull/1231).
- ec2_vpc_endpoint - Fix idempotency when creating endpoints (https://github.com/ansible-collections/amazon.aws/pull/1219).
- elb_application_lb - Fix idle_timeout handling (https://github.com/ansible-collections/amazon.aws/pull/1255).

v5.2.0
=======

Release Summary
---------------

This release contains several minor features and bugfixes.

Minor Changes
-------------

- autoscaling_group - Add support for ``default_cooldown`` option (https://github.com/ansible-collections/amazon.aws/pull/1183).
- ec2_ami_info - Add ``deprecation_time`` return value (https://github.com/ansible-collections/amazon.aws/pull/1189).
- ec2_instance - Add support for ``ebs_optimized`` option (https://github.com/ansible-collections/amazon.aws/pull/1187).
- ec2_instance - Add support for ``iam_instance_profile`` option (https://github.com/ansible-collections/amazon.aws/pull/1195).
- ec2_vol - Add support for ``throughput`` option for gp3 volumes (https://github.com/ansible-collections/amazon.aws/pull/1201).
- elb_application_lb - Add support for ``access_logs`` option (https://github.com/ansible-collections/amazon.aws/pull/1199).
- elb_application_lb_info - Add ``access_logs`` return value (https://github.com/ansible-collections/amazon.aws/pull/1199).
- iam_user - Add support for ``tags`` option (https://github.com/ansible-collections/amazon.aws/pull/1173).
- rds_instance - Add support for ``db_parameter_group_name`` option (https://github.com/ansible-collections/amazon.aws/pull/1178).
- secretsmanager_secret - Add support for ``replica_regions`` option (https://github.com/ansible-collections/amazon.aws/pull/1176).

Bugfixes
--------

- cloudwatch_metric_alarm - Fix ``unit`` option not being applied (https://github.com/ansible-collections/amazon.aws/pull/1167).
- ec2_launch_template - Fix idempotency issue with ``instance_initiated_shutdown_behavior`` (https://github.com/ansible-collections/amazon.aws/pull/1181).
- elb_application_lb - Fix rule ordering when creating listeners (https://github.com/ansible-collections/amazon.aws/pull/1199).
- s3_bucket - Fix ``requester_pays`` option not being applied correctly (https://github.com/ansible-collections/amazon.aws/pull/1164).

v5.1.0
=======

Release Summary
---------------

This release contains several minor features and bugfixes.

Minor Changes
-------------

- ec2_instance - Add ``instance_metadata_tags`` option (https://github.com/ansible-collections/amazon.aws/pull/1127).
- ec2_launch_template - Add ``instance_metadata_tags`` option (https://github.com/ansible-collections/amazon.aws/pull/1127).
- ec2_vpc_subnet - Add support for ``enable_dns64`` option (https://github.com/ansible-collections/amazon.aws/pull/1115).
- elb_application_lb - Add ``routing_http_desync_mitigation_mode`` option (https://github.com/ansible-collections/amazon.aws/pull/1138).
- iam_role_info - Add ``attached_policies`` return value (https://github.com/ansible-collections/amazon.aws/pull/1120).
- s3_bucket - Add ``intelligent_tiering`` option (https://github.com/ansible-collections/amazon.aws/pull/1107).
- s3_bucket_info - Add ``intelligent_tiering_configuration`` return value (https://github.com/ansible-collections/amazon.aws/pull/1107).

Bugfixes
--------

- ec2_eip - Fix ``reuse_existing_ip_allowed`` behavior when ``tag_name`` is not specified (https://github.com/ansible-collections/amazon.aws/pull/1112).
- ec2_vol - Fix ``modify_volume`` for volumes in use (https://github.com/ansible-collections/amazon.aws/pull/1105).
- elb_application_lb - Fix ``idle_timeout`` handling (https://github.com/ansible-collections/amazon.aws/pull/1138).
- iam_policy - Fix ``detach`` option not being applied (https://github.com/ansible-collections/amazon.aws/pull/1098).

v5.0.0
=======

Release Summary
---------------

This major release brings updated minimum requirements and several new features. This release drops support for ``ansible-core<2.11`` and Python versions before 3.6.

Major Changes
-------------

- amazon.aws collection - Due to the end of support for Python 2.7 and Python 3.5, support for Python versions before Python 3.6 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1057).
- amazon.aws collection - Support for ansible-core < 2.11 has been dropped (https://github.com/ansible-collections/amazon.aws/pull/1062).

Minor Changes
-------------

- ec2_ami - Add support for ``launch_permission`` option (https://github.com/ansible-collections/amazon.aws/pull/1040).
- ec2_eni - Add support for ``attachment`` option (https://github.com/ansible-collections/amazon.aws/pull/1049).
- ec2_instance - Add support for ``nitro_enclave_options`` option (https://github.com/ansible-collections/amazon.aws/pull/1048).
- ec2_vpc_nat_gateway - Add support for ``secondary_allocation_ids`` option (https://github.com/ansible-collections/amazon.aws/pull/1035).
- elb_application_lb - Add support for ``waf_fail_open`` option (https://github.com/ansible-collections/amazon.aws/pull/1053).
- iam_role - Add ``boundary`` option (https://github.com/ansible-collections/amazon.aws/pull/1043).
- s3_bucket - Add support for ``block_public_acls`` and ``block_public_policy`` options (https://github.com/ansible-collections/amazon.aws/pull/1051).

Bugfixes
--------

- cloudformation - Fix ``state: absent`` not waiting for stack deletion to complete (https://github.com/ansible-collections/amazon.aws/pull/1028).
- ec2_ami - Fix ``tags`` option not being applied correctly (https://github.com/ansible-collections/amazon.aws/pull/1040).
- ec2_vol - Fix idempotency when modifying IOPS (https://github.com/ansible-collections/amazon.aws/pull/1022).
- elb_application_lb - Fix ``rules`` option not being applied correctly (https://github.com/ansible-collections/amazon.aws/pull/1016).
