# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import sys
import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.ansible_release import __version__
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six import binary_type
from ansible.module_utils.six import string_types
from ansible.module_utils.six import text_type
from ansible.module_utils.six import integer_types
# Used to live here, moved into ansible.module_utils.common.dict_transformations
from ansible.module_utils.common.dict_transformations import _camel_to_snake  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import _snake_to_camel  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict  # pylint: disable=unused-import

from .cloud import CloudRetry
# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.tagging
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict
from .tagging import compare_aws_tags

# Used to live here, moved into # ansible_collections.amazon.aws.plugins.module_utils.policy
from .policy import _py3cmp as py3cmp  # pylint: disable=unused-import
from .policy import compare_policies  # pylint: disable=unused-import
from .policy import sort_json_policy_dict  # pylint: disable=unused-import

BOTO_IMP_ERR = None
try:
    import boto
    import boto.ec2  # boto does weird import stuff
    HAS_BOTO = True
except ImportError:
    BOTO_IMP_ERR = traceback.format_exc()
    HAS_BOTO = False

BOTO3_IMP_ERR = None
try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    BOTO3_IMP_ERR = traceback.format_exc()
    HAS_BOTO3 = False


class AnsibleAWSError(Exception):
    pass


def _botocore_exception_maybe():
    """
    Allow for boto3 not being installed when using these utils by wrapping
    botocore.exceptions instead of assigning from it directly.
    """
    if HAS_BOTO3:
        return botocore.exceptions.ClientError
    return type(None)


class AWSRetry(CloudRetry):
    base_class = _botocore_exception_maybe()

    @staticmethod
    def status_code_from_exception(error):
        return error.response['Error']['Code']

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        # This list of failures is based on this API Reference
        # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html
        #
        # TooManyRequestsException comes from inside botocore when it
        # does retrys, unfortunately however it does not try long
        # enough to allow some services such as API Gateway to
        # complete configuration.  At the moment of writing there is a
        # botocore/boto3 bug open to fix this.
        #
        # https://github.com/boto/boto3/issues/876 (and linked PRs etc)
        retry_on = [
            'RequestLimitExceeded', 'Unavailable', 'ServiceUnavailable',
            'InternalFailure', 'InternalError', 'TooManyRequestsException',
            'Throttling'
        ]
        if catch_extra_error_codes:
            retry_on.extend(catch_extra_error_codes)

        return response_code in retry_on


def boto3_conn(module, conn_type=None, resource=None, region=None, endpoint=None, **params):
    try:
        return _boto3_conn(conn_type=conn_type, resource=resource, region=region, endpoint=endpoint, **params)
    except ValueError as e:
        module.fail_json(msg="Couldn't connect to AWS: %s" % to_native(e))
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError,
            botocore.exceptions.NoCredentialsError, botocore.exceptions.ConfigParseError) as e:
        module.fail_json(msg=to_native(e))
    except botocore.exceptions.NoRegionError as e:
        module.fail_json(msg="The %s module requires a region and none was found in configuration, "
                         "environment variables or module parameters" % module._name)


def _boto3_conn(conn_type=None, resource=None, region=None, endpoint=None, **params):
    profile = params.pop('profile_name', None)

    if conn_type not in ['both', 'resource', 'client']:
        raise ValueError('There is an issue in the calling code. You '
                         'must specify either both, resource, or client to '
                         'the conn_type parameter in the boto3_conn function '
                         'call')

    config = botocore.config.Config(
        user_agent_extra='Ansible/{0}'.format(__version__),
    )

    if params.get('config') is not None:
        config = config.merge(params.pop('config'))
    if params.get('aws_config') is not None:
        config = config.merge(params.pop('aws_config'))

    session = boto3.session.Session(
        profile_name=profile,
    )

    if conn_type == 'resource':
        return session.resource(resource, config=config, region_name=region, endpoint_url=endpoint, **params)
    elif conn_type == 'client':
        return session.client(resource, config=config, region_name=region, endpoint_url=endpoint, **params)
    else:
        client = session.client(resource, region_name=region, endpoint_url=endpoint, **params)
        resource = session.resource(resource, region_name=region, endpoint_url=endpoint, **params)
        return client, resource


boto3_inventory_conn = _boto3_conn


def boto_exception(err):
    """
    Extracts the error message from a boto exception.

    :param err: Exception from boto
    :return: Error message
    """
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = str(err.message) + ' ' + str(err) + ' - ' + str(type(err))
    else:
        error = '%s: %s' % (Exception, err)

    return error


def aws_common_argument_spec():
    return dict(
        debug_botocore_endpoint_logs=dict(fallback=(env_fallback, ['ANSIBLE_DEBUG_BOTOCORE_LOGS']), default=False, type='bool'),
        ec2_url=dict(aliases=['aws_endpoint_url', 'endpoint_url']),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key'], no_log=False),
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        security_token=dict(aliases=['access_token', 'aws_security_token', 'session_token', 'aws_session_token'], no_log=True),
        validate_certs=dict(default=True, type='bool'),
        aws_ca_bundle=dict(type='path'),
        profile=dict(aliases=['aws_profile']),
        aws_config=dict(type='dict'),
    )


def ec2_argument_spec():
    spec = aws_common_argument_spec()
    spec.update(
        dict(
            region=dict(aliases=['aws_region', 'ec2_region']),
        )
    )
    return spec


def get_aws_region(module, boto3=False):
    region = module.params.get('region')

    if region:
        return region

    if 'AWS_REGION' in os.environ:
        return os.environ['AWS_REGION']
    if 'AWS_DEFAULT_REGION' in os.environ:
        return os.environ['AWS_DEFAULT_REGION']
    if 'EC2_REGION' in os.environ:
        return os.environ['EC2_REGION']

    if not boto3:
        if not HAS_BOTO:
            module.fail_json(msg=missing_required_lib('boto'), exception=BOTO_IMP_ERR)
        # boto.config.get returns None if config not found
        region = boto.config.get('Boto', 'aws_region')
        if region:
            return region
        return boto.config.get('Boto', 'ec2_region')

    if not HAS_BOTO3:
        module.fail_json(msg=missing_required_lib('boto3'), exception=BOTO3_IMP_ERR)

    # here we don't need to make an additional call, will default to 'us-east-1' if the below evaluates to None.
    try:
        profile_name = module.params.get('profile')
        return botocore.session.Session(profile=profile_name).get_config_variable('region')
    except botocore.exceptions.ProfileNotFound as e:
        return None


def get_aws_connection_info(module, boto3=False):

    # Check module args for credentials, then check environment vars
    # access_key

    ec2_url = module.params.get('ec2_url')
    access_key = module.params.get('aws_access_key')
    secret_key = module.params.get('aws_secret_key')
    security_token = module.params.get('security_token')
    region = get_aws_region(module, boto3)
    profile_name = module.params.get('profile')
    validate_certs = module.params.get('validate_certs')
    ca_bundle = module.params.get('aws_ca_bundle')
    config = module.params.get('aws_config')

    # Only read the profile environment variables if we've *not* been passed
    # any credentials as parameters.
    if not profile_name and not access_key and not secret_key:
        if os.environ.get('AWS_PROFILE'):
            profile_name = os.environ.get('AWS_PROFILE')
        if os.environ.get('AWS_DEFAULT_PROFILE'):
            profile_name = os.environ.get('AWS_DEFAULT_PROFILE')

    if profile_name and (access_key or secret_key or security_token):
        module.deprecate("Passing both a profile and access tokens has been deprecated."
                         "  Only the profile will be used."
                         "  In later versions of Ansible the options will be mutually exclusive",
                         date='2022-06-01', collection_name='amazon.aws')

    if not ec2_url:
        if 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']
        elif 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']

    if not access_key:
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            access_key = os.environ['AWS_ACCESS_KEY_ID']
        elif os.environ.get('AWS_ACCESS_KEY'):
            access_key = os.environ['AWS_ACCESS_KEY']
        elif os.environ.get('EC2_ACCESS_KEY'):
            access_key = os.environ['EC2_ACCESS_KEY']
        elif HAS_BOTO and boto.config.get('Credentials', 'aws_access_key_id'):
            access_key = boto.config.get('Credentials', 'aws_access_key_id')
        elif HAS_BOTO and boto.config.get('default', 'aws_access_key_id'):
            access_key = boto.config.get('default', 'aws_access_key_id')
        else:
            # in case access_key came in as empty string
            access_key = None

    if not secret_key:
        if os.environ.get('AWS_SECRET_ACCESS_KEY'):
            secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        elif os.environ.get('AWS_SECRET_KEY'):
            secret_key = os.environ['AWS_SECRET_KEY']
        elif os.environ.get('EC2_SECRET_KEY'):
            secret_key = os.environ['EC2_SECRET_KEY']
        elif HAS_BOTO and boto.config.get('Credentials', 'aws_secret_access_key'):
            secret_key = boto.config.get('Credentials', 'aws_secret_access_key')
        elif HAS_BOTO and boto.config.get('default', 'aws_secret_access_key'):
            secret_key = boto.config.get('default', 'aws_secret_access_key')
        else:
            # in case secret_key came in as empty string
            secret_key = None

    if not security_token:
        if os.environ.get('AWS_SECURITY_TOKEN'):
            security_token = os.environ['AWS_SECURITY_TOKEN']
        elif os.environ.get('AWS_SESSION_TOKEN'):
            security_token = os.environ['AWS_SESSION_TOKEN']
        elif os.environ.get('EC2_SECURITY_TOKEN'):
            security_token = os.environ['EC2_SECURITY_TOKEN']
        elif HAS_BOTO and boto.config.get('Credentials', 'aws_security_token'):
            security_token = boto.config.get('Credentials', 'aws_security_token')
        elif HAS_BOTO and boto.config.get('default', 'aws_security_token'):
            security_token = boto.config.get('default', 'aws_security_token')
        else:
            # in case secret_token came in as empty string
            security_token = None

    if not ca_bundle:
        if os.environ.get('AWS_CA_BUNDLE'):
            ca_bundle = os.environ.get('AWS_CA_BUNDLE')

    if HAS_BOTO3 and boto3:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           aws_session_token=security_token)

        if profile_name:
            boto_params = dict(aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None)
            boto_params['profile_name'] = profile_name

        if validate_certs and ca_bundle:
            boto_params['verify'] = ca_bundle
        else:
            boto_params['verify'] = validate_certs

    else:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           security_token=security_token)

        # only set profile_name if passed as an argument
        if profile_name:
            boto_params['profile_name'] = profile_name

        boto_params['validate_certs'] = validate_certs

    if config is not None:
        if HAS_BOTO3 and boto3:
            boto_params['aws_config'] = botocore.config.Config(**config)
        elif HAS_BOTO and not boto3:
            if 'user_agent' in config:
                sys.modules["boto.connection"].UserAgent = config['user_agent']

    for param, value in boto_params.items():
        if isinstance(value, binary_type):
            boto_params[param] = text_type(value, 'utf-8', 'strict')

    return region, ec2_url, boto_params


def get_ec2_creds(module):
    ''' for compatibility mode with old modules that don't/can't yet
        use ec2_connect method '''
    region, ec2_url, boto_params = get_aws_connection_info(module)
    return ec2_url, boto_params['aws_access_key_id'], boto_params['aws_secret_access_key'], region


def boto_fix_security_token_in_profile(conn, profile_name):
    ''' monkey patch for boto issue boto/boto#2100 '''
    profile = 'profile ' + profile_name
    if boto.config.has_option(profile, 'aws_security_token'):
        conn.provider.set_security_token(boto.config.get(profile, 'aws_security_token'))
    return conn


def connect_to_aws(aws_module, region, **params):
    try:
        conn = aws_module.connect_to_region(region, **params)
    except(boto.provider.ProfileNotFoundError):
        raise AnsibleAWSError("Profile given for AWS was not found.  Please fix and retry.")
    if not conn:
        if region not in [aws_module_region.name for aws_module_region in aws_module.regions()]:
            raise AnsibleAWSError("Region %s does not seem to be available for aws module %s. If the region definitely exists, you may need to upgrade "
                                  "boto or extend with endpoints_path" % (region, aws_module.__name__))
        else:
            raise AnsibleAWSError("Unknown problem connecting to region %s for aws module %s." % (region, aws_module.__name__))
    if params.get('profile_name'):
        conn = boto_fix_security_token_in_profile(conn, params['profile_name'])
    return conn


def ec2_connect(module):

    """ Return an ec2 connection"""

    region, ec2_url, boto_params = get_aws_connection_info(module)

    # If ec2_url is present use it
    if ec2_url:
        try:
            ec2 = boto.connect_ec2_endpoint(ec2_url, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError, boto.provider.ProfileNotFoundError) as e:
            module.fail_json(msg=str(e))
    # Otherwise, if we have a region specified, connect to its endpoint.
    elif region:
        try:
            ec2 = connect_to_aws(boto.ec2, region, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError, boto.provider.ProfileNotFoundError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="Either region or ec2_url must be specified")

    return ec2


def ansible_dict_to_boto3_filter_list(filters_dict):

    """ Convert an Ansible dict of filters to list of dicts that boto3 can use
    Args:
        filters_dict (dict): Dict of AWS filters.
    Basic Usage:
        >>> filters = {'some-aws-id': 'i-01234567'}
        >>> ansible_dict_to_boto3_filter_list(filters)
        {
            'some-aws-id': 'i-01234567'
        }
    Returns:
        List: List of AWS filters and their values
        [
            {
                'Name': 'some-aws-id',
                'Values': [
                    'i-01234567',
                ]
            }
        ]
    """

    filters_list = []
    for k, v in filters_dict.items():
        filter_dict = {'Name': k}
        if isinstance(v, bool):
            filter_dict['Values'] = [str(v).lower()]
        elif isinstance(v, integer_types):
            filter_dict['Values'] = [str(v)]
        elif isinstance(v, string_types):
            filter_dict['Values'] = [v]
        else:
            filter_dict['Values'] = v

        filters_list.append(filter_dict)

    return filters_list


def get_ec2_security_group_ids_from_names(sec_group_list, ec2_connection, vpc_id=None, boto3=True):

    """ Return list of security group IDs from security group names. Note that security group names are not unique
     across VPCs.  If a name exists across multiple VPCs and no VPC ID is supplied, all matching IDs will be returned. This
     will probably lead to a boto exception if you attempt to assign both IDs to a resource so ensure you wrap the call in
     a try block
     """

    def get_sg_name(sg, boto3):

        if boto3:
            return sg['GroupName']
        else:
            return sg.name

    def get_sg_id(sg, boto3):

        if boto3:
            return sg['GroupId']
        else:
            return sg.id

    sec_group_id_list = []

    if isinstance(sec_group_list, string_types):
        sec_group_list = [sec_group_list]

    # Get all security groups
    if boto3:
        if vpc_id:
            filters = [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id,
                    ]
                }
            ]
            all_sec_groups = ec2_connection.describe_security_groups(Filters=filters)['SecurityGroups']
        else:
            all_sec_groups = ec2_connection.describe_security_groups()['SecurityGroups']
    else:
        if vpc_id:
            filters = {'vpc-id': vpc_id}
            all_sec_groups = ec2_connection.get_all_security_groups(filters=filters)
        else:
            all_sec_groups = ec2_connection.get_all_security_groups()

    unmatched = set(sec_group_list).difference(str(get_sg_name(all_sg, boto3)) for all_sg in all_sec_groups)
    sec_group_name_list = list(set(sec_group_list) - set(unmatched))

    if len(unmatched) > 0:
        # If we have unmatched names that look like an ID, assume they are
        sec_group_id_list[:] = [sg for sg in unmatched if re.match('sg-[a-fA-F0-9]+$', sg)]
        still_unmatched = [sg for sg in unmatched if not re.match('sg-[a-fA-F0-9]+$', sg)]
        if len(still_unmatched) > 0:
            raise ValueError("The following group names are not valid: %s" % ', '.join(still_unmatched))

    sec_group_id_list += [str(get_sg_id(all_sg, boto3)) for all_sg in all_sec_groups if str(get_sg_name(all_sg, boto3)) in sec_group_name_list]

    return sec_group_id_list


def map_complex_type(complex_type, type_map):
    """
        Allows to cast elements within a dictionary to a specific type
        Example of usage:

        DEPLOYMENT_CONFIGURATION_TYPE_MAP = {
            'maximum_percent': 'int',
            'minimum_healthy_percent': 'int'
        }

        deployment_configuration = map_complex_type(module.params['deployment_configuration'],
                                                    DEPLOYMENT_CONFIGURATION_TYPE_MAP)

        This ensures all keys within the root element are casted and valid integers
    """

    if complex_type is None:
        return
    new_type = type(complex_type)()
    if isinstance(complex_type, dict):
        for key in complex_type:
            if key in type_map:
                if isinstance(type_map[key], list):
                    new_type[key] = map_complex_type(
                        complex_type[key],
                        type_map[key][0])
                else:
                    new_type[key] = map_complex_type(
                        complex_type[key],
                        type_map[key])
            else:
                return complex_type
    elif isinstance(complex_type, list):
        for i in range(len(complex_type)):
            new_type.append(map_complex_type(
                complex_type[i],
                type_map))
    elif type_map:
        return globals()['__builtins__'][type_map](complex_type)
    return new_type


@AWSRetry.jittered_backoff()
def _describe_ec2_tags(client, **params):
    paginator = client.get_paginator('describe_tags')
    return paginator.paginate(**params).build_full_result()


def add_ec2_tags(client, module, resource_id, tags_to_set, retry_codes=None):
    """
    Sets Tags on an EC2 resource.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param tags_to_set: A dictionary of key/value pairs to set
    :param retry_codes: additional boto3 error codes to trigger retries
    """

    if not tags_to_set:
        return False
    if module.check_mode:
        return True

    if not retry_codes:
        retry_codes = []

    try:
        tags_to_add = ansible_dict_to_boto3_tag_list(tags_to_set)
        AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(
            client.create_tags
        )(
            Resources=[resource_id], Tags=tags_to_add
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to add tags {0} to {1}".format(tags_to_set, resource_id))
    return True


def remove_ec2_tags(client, module, resource_id, tags_to_unset, retry_codes=None):
    """
    Removes Tags from an EC2 resource.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param tags_to_unset: a list of tag keys to removes
    :param retry_codes: additional boto3 error codes to trigger retries
    """

    if not tags_to_unset:
        return False
    if module.check_mode:
        return True

    if not retry_codes:
        retry_codes = []

    tags_to_remove = [dict(Key=tagkey) for tagkey in tags_to_unset]

    try:
        AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(
            client.delete_tags
        )(
            Resources=[resource_id], Tags=tags_to_remove
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to delete tags {0} from {1}".format(tags_to_unset, resource_id))
    return True


def describe_ec2_tags(client, module, resource_id, resource_type=None, retry_codes=None):
    """
    Performs a paginated search of EC2 resource tags.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param resource_type: the type of the resource
    :param retry_codes: additional boto3 error codes to trigger retries
    """
    filters = {'resource-id': resource_id}
    if resource_type:
        filters['resource-type'] = resource_type
    filters = ansible_dict_to_boto3_filter_list(filters)

    if not retry_codes:
        retry_codes = []

    try:
        results = AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(
            _describe_ec2_tags
        )(
            client, Filters=filters
        )
        return boto3_tag_list_to_ansible_dict(results.get('Tags', None))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe tags for EC2 Resource: {0}".format(resource_id))


def ensure_ec2_tags(client, module, resource_id, resource_type=None, tags=None, purge_tags=True, retry_codes=None):
    """
    Updates the tags on an EC2 resource.

    To remove all tags the tags parameter must be explicitly set to an empty dictionary.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param resource_type: the type of the resource
    :param tags: the Tags to apply to the resource
    :param purge_tags: whether tags missing from the tag list should be removed
    :param retry_codes: additional boto3 error codes to trigger retries
    :return: changed: returns True if the tags are changed
    """

    if tags is None:
        return False

    if not retry_codes:
        retry_codes = []

    changed = False
    current_tags = describe_ec2_tags(client, module, resource_id, resource_type, retry_codes)

    tags_to_set, tags_to_unset = compare_aws_tags(current_tags, tags, purge_tags)

    if purge_tags and not tags:
        tags_to_unset = current_tags

    changed |= remove_ec2_tags(client, module, resource_id, tags_to_unset, retry_codes)
    changed |= add_ec2_tags(client, module, resource_id, tags_to_set, retry_codes)

    return changed


def normalize_ec2_vpc_dhcp_config(option_config):
    """
    The boto2 module returned a config dict, but boto3 returns a list of dicts
    Make the data we return look like the old way, so we don't break users.
    This is also much more user-friendly.
    boto3:
        'DhcpConfigurations': [
            {'Key': 'domain-name', 'Values': [{'Value': 'us-west-2.compute.internal'}]},
            {'Key': 'domain-name-servers', 'Values': [{'Value': 'AmazonProvidedDNS'}]},
            {'Key': 'netbios-name-servers', 'Values': [{'Value': '1.2.3.4'}, {'Value': '5.6.7.8'}]},
            {'Key': 'netbios-node-type', 'Values': [1]},
            {'Key': 'ntp-servers', 'Values': [{'Value': '1.2.3.4'}, {'Value': '5.6.7.8'}]}
        ],
    The module historically returned:
        "new_options": {
            "domain-name": "ec2.internal",
            "domain-name-servers": ["AmazonProvidedDNS"],
            "netbios-name-servers": ["10.0.0.1", "10.0.1.1"],
            "netbios-node-type": "1",
            "ntp-servers": ["10.0.0.2", "10.0.1.2"]
        },
    """
    config_data = {}

    if len(option_config) == 0:
        # If there is no provided config, return the empty dictionary
        return config_data

    for config_item in option_config:
        # Handle single value keys
        if config_item['Key'] == 'netbios-node-type':
            if isinstance(config_item['Values'], integer_types):
                config_data['netbios-node-type'] = str((config_item['Values']))
            elif isinstance(config_item['Values'], list):
                config_data['netbios-node-type'] = str((config_item['Values'][0]['Value']))
        # Handle actual lists of values
        for option in ['domain-name', 'domain-name-servers', 'ntp-servers', 'netbios-name-servers']:
            if config_item['Key'] == option:
                config_data[option] = [val['Value'] for val in config_item['Values']]

    return config_data


def is_outposts_arn(input_regex):
    """
    Validates the provided regex pattern of outpost arn as per API specification document.

    API Specification Document:
    https://docs.aws.amazon.com/outposts/latest/APIReference/API_Outpost.html
    """
    regex_pattern = r'^arn:aws([a-z-]+)?:outposts:[a-z\d-]+:\d{12}:outpost/op-[a-f0-9]{17}$'
    if not re.match(regex_pattern, input_regex):
        return False
    return True
