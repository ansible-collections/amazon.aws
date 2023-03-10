# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Will Thames <will@thames.id.au>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Common configuration for all AWS services
    # Note: If you're updating MODULES, PLUGINS probably needs updating too.

    # Formatted for Modules
    # - modules don't support 'env'
    MODULES = r"""
options:
  access_key:
    description:
      - AWS access key ID.
      - See the AWS documentation for more information about access tokens
        U(https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).
      - The C(AWS_ACCESS_KEY_ID), C(AWS_ACCESS_KEY) or C(EC2_ACCESS_KEY)
        environment variables may also be used in decreasing order of
        preference.
      - The I(aws_access_key) and I(profile) options are mutually exclusive.
      - The I(aws_access_key_id) alias was added in release 5.1.0 for
        consistency with the AWS botocore SDK.
      - The I(ec2_access_key) alias has been deprecated and will be removed in a
        release after 2024-12-01.
      - Support for the C(EC2_ACCESS_KEY) environment variable has been
        deprecated and will be removed in a release after 2024-12-01.
    type: str
    aliases: ['aws_access_key_id', 'aws_access_key', 'ec2_access_key']
  secret_key:
    description:
      - AWS secret access key.
      - See the AWS documentation for more information about access tokens
        U(https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).
      - The C(AWS_SECRET_ACCESS_KEY), C(AWS_SECRET_KEY), or C(EC2_SECRET_KEY)
        environment variables may also be used in decreasing order of
        preference.
      - The I(secret_key) and I(profile) options are mutually exclusive.
      - The I(aws_secret_access_key) alias was added in release 5.1.0 for
        consistency with the AWS botocore SDK.
      - The I(ec2_secret_key) alias has been deprecated and will be removed in a
        release after 2024-12-01.
      - Support for the C(EC2_SECRET_KEY) environment variable has been
        deprecated and will be removed in a release after 2024-12-01.
    type: str
    aliases: ['aws_secret_access_key', 'aws_secret_key', 'ec2_secret_key']
  session_token:
    description:
      - AWS STS session token for use with temporary credentials.
      - See the AWS documentation for more information about access tokens
        U(https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).
      - The C(AWS_SESSION_TOKEN), C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN)
        environment variables may also be used in decreasing order of preference.
      - The I(security_token) and I(profile) options are mutually exclusive.
      - Aliases I(aws_session_token) and I(session_token) were added in release
        3.2.0, with the parameter being renamed from I(security_token) to
        I(session_token) in release 6.0.0.
      - The I(security_token), I(aws_security_token), and I(access_token)
        aliases have been deprecated and will be removed in a release after
        2024-12-01.
      - Support for the C(EC2_SECRET_KEY) and C(AWS_SECURITY_TOKEN) environment
        variables has been deprecated and will be removed in a release after
        2024-12-01.
    type: str
    aliases: ['aws_session_token', 'security_token', 'aws_security_token', 'access_token']
  profile:
    description:
      - A named AWS profile to use for authentication.
      - See the AWS documentation for more information about named profiles
        U(https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html).
      - The C(AWS_PROFILE) environment variable may also be used.
      - The I(profile) option is mutually exclusive with the I(aws_access_key),
        I(aws_secret_key) and I(security_token) options.
    type: str
    aliases: ['aws_profile']

  endpoint_url:
    description:
      - URL to connect to instead of the default AWS endpoints.  While this
        can be used to connection to other AWS-compatible services the
        amazon.aws and community.aws collections are only tested against
        AWS.
      - The  C(AWS_URL) or C(EC2_URL) environment variables may also be used,
        in decreasing order of preference.
      - The I(ec2_url) and I(s3_url) aliases have been deprecated and will be
        removed in a release after 2024-12-01.
      - Support for the C(EC2_URL) environment variable has been deprecated and
        will be removed in a release after 2024-12-01.
    type: str
    aliases: ['ec2_url', 'aws_endpoint_url', 's3_url' ]

  aws_ca_bundle:
    description:
      - The location of a CA Bundle to use when validating SSL certificates.
      - The C(AWS_CA_BUNDLE) environment variable may also be used.
    type: path
  validate_certs:
    description:
      - When set to C(false), SSL certificates will not be validated for
        communication with the AWS APIs.
      - Setting I(validate_certs=false) is strongly discouraged, as an
        alternative, consider setting I(aws_ca_bundle) instead.
    type: bool
    default: true
  aws_config:
    description:
      - A dictionary to modify the botocore configuration.
      - Parameters can be found in the AWS documentation
        U(https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config).
    type: dict
  debug_botocore_endpoint_logs:
    description:
      - Use a C(botocore.endpoint) logger to parse the unique (rather than total)
        C("resource:action") API calls made during a task, outputing the set to
        the resource_actions key in the task results. Use the
        C(aws_resource_action) callback to output to total list made during
        a playbook.
      - The C(ANSIBLE_DEBUG_BOTOCORE_LOGS) environment variable may also be used.
    type: bool
    default: false
notes:
  - B(Caution:) For modules, environment variables and configuration files are
    read from the Ansible 'host' context and not the 'controller' context.
    As such, files may need to be explicitly copied to the 'host'.  For lookup
    and connection plugins, environment variables and configuration files are
    read from the Ansible 'controller' context and not the 'host' context.
  - The AWS SDK (boto3) that Ansible uses may also read defaults for credentials
    and other settings, such as the region, from its configuration files in the
    Ansible 'host' context (typically C(~/.aws/credentials)).
    See U(https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
    for more information.
"""

    # Formatted for non-module plugins
    # - modules don't support 'env'
    PLUGINS = r"""
options:
  access_key:
    description:
      - AWS access key ID.
      - See the AWS documentation for more information about access tokens
        U(https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).
      - The I(aws_access_key) and I(profile) options are mutually exclusive.
      - The I(aws_access_key_id) alias was added in release 5.1.0 for
        consistency with the AWS botocore SDK.
      - The I(ec2_access_key) alias has been deprecated and will be removed in a
        release after 2024-12-01.
    type: str
    aliases: ['aws_access_key_id', 'aws_access_key', 'ec2_access_key']
    env:
      - name: AWS_ACCESS_KEY_ID
      - name: AWS_ACCESS_KEY
      - name: EC2_ACCESS_KEY
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_ACCESS_KEY_ID
  secret_key:
    description:
      - AWS secret access key.
      - See the AWS documentation for more information about access tokens
        U(https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).
      - The I(secret_key) and I(profile) options are mutually exclusive.
      - The I(aws_secret_access_key) alias was added in release 5.1.0 for
        consistency with the AWS botocore SDK.
      - The I(ec2_secret_key) alias has been deprecated and will be removed in a
        release after 2024-12-01.
    type: str
    aliases: ['aws_secret_access_key', 'aws_secret_key', 'ec2_secret_key']
    env:
      - name: AWS_SECRET_ACCESS_KEY
      - name: AWS_SECRET_KEY
      - name: EC2_SECRET_KEY
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_SECRET_ACCESS_KEY
  session_token:
    description:
      - AWS STS session token for use with temporary credentials.
      - See the AWS documentation for more information about access tokens
        U(https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).
      - The I(security_token) and I(profile) options are mutually exclusive.
      - Aliases I(aws_session_token) and I(session_token) were added in release
        3.2.0, with the parameter being renamed from I(security_token) to
        I(session_token) in release 6.0.0.
      - The I(security_token), I(aws_security_token), and I(access_token)
        aliases have been deprecated and will be removed in a release after
        2024-12-01.
    type: str
    aliases: ['aws_session_token', 'security_token', 'aws_security_token', 'access_token']
    env:
      - name: AWS_SESSION_TOKEN
      - name: AWS_SECURITY_TOKEN
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'AWS_SECURITY_TOKEN was used for compatibility with the original boto SDK, support for which has been dropped'
          alternatives: AWS_SESSION_TOKEN
      - name: EC2_SECURITY_TOKEN
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_SESSION_TOKEN

  profile:
    description:
      - A named AWS profile to use for authentication.
      - See the AWS documentation for more information about named profiles
        U(https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html).
      - The I(profile) option is mutually exclusive with the I(aws_access_key),
        I(aws_secret_key) and I(security_token) options.
      - The I(boto_profile) alias has been deprecated and will be removed in a
        release after 2024-12-01.
    type: str
    aliases: ['aws_profile', 'boto_profile']
    env:
      - name: AWS_PROFILE
      - name: AWS_DEFAULT_PROFILE
  endpoint_url:
    description:
      - URL to connect to instead of the default AWS endpoints.  While this
        can be used to connection to other AWS-compatible services the
        amazon.aws and community.aws collections are only tested against
        AWS.
      - The I(endpoint) alias has been deprecated and will be
        removed in a release after 2024-12-01.
    type: str
    aliases: ['aws_endpoint_url', 'endpoint' ]
    env:
      - name: AWS_URL
      - name: EC2_URL
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_URL

notes:
  - B(Caution:) For modules, environment variables and configuration files are
    read from the Ansible 'host' context and not the 'controller' context.
    As such, files may need to be explicitly copied to the 'host'.  For lookup
    and connection plugins, environment variables and configuration files are
    read from the Ansible 'controller' context and not the 'host' context.
  - The AWS SDK (boto3) that Ansible uses may also read defaults for credentials
    and other settings, such as the region, from its configuration files in the
    Ansible 'host' context (typically C(~/.aws/credentials)).
    See U(https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
    for more information.
"""
