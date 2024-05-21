# -*- coding: utf-8 -*-

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

"""
A set of helper functions designed to help with initializing boto3/botocore
connections.
"""

import json
import os
import traceback

BOTO3_IMP_ERR = None
try:
    import boto3
    import botocore

    HAS_BOTO3 = True
except ImportError:
    BOTO3_IMP_ERR = traceback.format_exc()
    HAS_BOTO3 = False

try:
    from packaging.version import Version

    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

from ansible.module_utils._text import to_native
from ansible.module_utils.ansible_release import __version__
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six import binary_type
from ansible.module_utils.six import text_type

from .common import get_collection_info
from .exceptions import AnsibleBotocoreError
from .retries import AWSRetry

MINIMUM_BOTOCORE_VERSION = "1.29.0"
MINIMUM_BOTO3_VERSION = "1.26.0"


def _get_user_agent_string():
    info = get_collection_info()
    result = f"APN/1.0 Ansible/{__version__}"
    if info["name"]:
        if info["version"] is not None:
            result += f" {info['name']}/{info['version']}"
        else:
            result += f" {info['name']}"
    return result


def boto3_conn(module, conn_type=None, resource=None, region=None, endpoint=None, **params):
    """
    Builds a boto3 resource/client connection cleanly wrapping the most common failures.
    Handles:
        ValueError,
        botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError,
        botocore.exceptions.NoCredentialsError, botocore.exceptions.ConfigParseError,
        botocore.exceptions.NoRegionError
    """
    try:
        return _boto3_conn(conn_type=conn_type, resource=resource, region=region, endpoint=endpoint, **params)
    except ValueError as e:
        module.fail_json(
            msg=f"Couldn't connect to AWS: {to_native(e)}",
        )
    except (
        botocore.exceptions.ProfileNotFound,
        botocore.exceptions.PartialCredentialsError,
        botocore.exceptions.NoCredentialsError,
        botocore.exceptions.ConfigParseError,
    ) as e:
        module.fail_json(
            msg=to_native(e),
        )
    except botocore.exceptions.NoRegionError:
        module.fail_json(
            msg=f"The {module._name} module requires a region and none was found in configuration, "
            "environment variables or module parameters",
        )


def _merge_botocore_config(config_a, config_b):
    """
    Merges the extra configuration options from config_b into config_a.
    Supports both botocore.config.Config objects and dicts
    """
    if not config_b:
        return config_a
    if not isinstance(config_b, botocore.config.Config):
        config_b = botocore.config.Config(**config_b)
    return config_a.merge(config_b)


def _boto3_conn(conn_type=None, resource=None, region=None, endpoint=None, **params):
    """
    Builds a boto3 resource/client connection cleanly wrapping the most common failures.
    No exceptions are caught/handled.
    """
    profile = params.pop("profile_name", None)

    if conn_type not in ["both", "resource", "client"]:
        raise ValueError(
            "There is an issue in the calling code. You "
            "must specify either both, resource, or client to "
            "the conn_type parameter in the boto3_conn function "
            "call"
        )

    # default config with user agent
    config = botocore.config.Config(
        user_agent=_get_user_agent_string(),
    )

    for param in ("config", "aws_config"):
        config = _merge_botocore_config(config, params.pop(param, None))

    session = boto3.session.Session(
        profile_name=profile,
    )

    enable_placebo(session)

    if conn_type == "resource":
        return session.resource(resource, config=config, region_name=region, endpoint_url=endpoint, **params)
    elif conn_type == "client":
        return session.client(resource, config=config, region_name=region, endpoint_url=endpoint, **params)
    else:
        client = session.client(resource, config=config, region_name=region, endpoint_url=endpoint, **params)
        resource = session.resource(resource, config=config, region_name=region, endpoint_url=endpoint, **params)
        return client, resource


# Inventory plugins don't have access to the same 'module', they need to throw
# an exception rather than calling module.fail_json
boto3_inventory_conn = _boto3_conn


def boto_exception(err):
    """
    Extracts the error message from a boto exception.

    :param err: Exception from boto
    :return: Error message
    """
    if hasattr(err, "error_message"):
        error = err.error_message
    elif hasattr(err, "message"):
        error = str(err.message) + " " + str(err) + " - " + str(type(err))
    else:
        error = f"{Exception}: {err}"

    return error


def _aws_region(params):
    region = params.get("region")

    if region:
        return region

    if not HAS_BOTO3:
        raise AnsibleBotocoreError(message=missing_required_lib("boto3 and botocore"), exception=BOTO3_IMP_ERR)

    # here we don't need to make an additional call, will default to 'us-east-1' if the below evaluates to None.
    try:
        # Botocore doesn't like empty strings, make sure we default to None in the case of an empty
        # string.
        profile_name = params.get("profile") or None
        return botocore.session.Session(profile=profile_name).get_config_variable("region")
    except botocore.exceptions.ProfileNotFound:
        return None


def get_aws_region(module, boto3=None):  # pylint: disable=redefined-outer-name
    if boto3 is not None:
        module.deprecate(
            "get_aws_region(): the boto3 parameter will be removed in a release after 2025-05-01. "
            "The parameter has been ignored since release 4.0.0.",
            date="2025-05-01",
            collection_name="amazon.aws",
        )
    try:
        return _aws_region(module.params)
    except AnsibleBotocoreError as e:
        if e.exception:
            module.fail_json(msg=e.message, exception=e.exception)
        else:
            module.fail_json(msg=e.message)


def _aws_connection_info(params):
    endpoint_url = params.get("endpoint_url")
    access_key = params.get("access_key")
    secret_key = params.get("secret_key")
    session_token = params.get("session_token")
    region = _aws_region(params)
    profile_name = params.get("profile")
    validate_certs = params.get("validate_certs")
    ca_bundle = params.get("aws_ca_bundle")
    config = params.get("aws_config")

    # Caught here so that they can be deliberately set to '' to avoid conflicts when environment
    # variables are also being used
    if profile_name and (access_key or secret_key or session_token):
        raise AnsibleBotocoreError(message="Passing both a profile and access tokens is not supported.")

    # Botocore doesn't like empty strings, make sure we default to None in the case of an empty
    # string.
    if not access_key:
        access_key = None
    if not secret_key:
        secret_key = None
    if not session_token:
        session_token = None

    if profile_name:
        boto_params = dict(
            aws_access_key_id=None,
            aws_secret_access_key=None,
            aws_session_token=None,
            profile_name=profile_name,
        )
    else:
        boto_params = dict(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

    if validate_certs and ca_bundle:
        boto_params["verify"] = ca_bundle
    else:
        boto_params["verify"] = validate_certs

    if config is not None:
        boto_params["aws_config"] = botocore.config.Config(**config)

    for param, value in boto_params.items():
        if isinstance(value, binary_type):
            boto_params[param] = text_type(value, "utf-8", "strict")

    return region, endpoint_url, boto_params


def get_aws_connection_info(module, boto3=None):  # pylint: disable=redefined-outer-name
    if boto3 is not None:
        module.deprecate(
            "get_aws_connection_info(): the boto3 parameter will be removed in a release after 2025-05-01. "
            "The parameter has been ignored since release 4.0.0.",
            date="2025-05-01",
            collection_name="amazon.aws",
        )
    try:
        return _aws_connection_info(module.params)
    except AnsibleBotocoreError as e:
        if e.exception:
            module.fail_json(msg=e.message, exception=e.exception)
        else:
            module.fail_json(msg=e.message)


def _paginated_query(client, paginator_name, **params):
    paginator = client.get_paginator(paginator_name)
    result = paginator.paginate(**params).build_full_result()
    return result


def paginated_query_with_retries(client, paginator_name, retry_decorator=None, **params):
    """
    Performs a boto3 paginated query.
    By default uses uses AWSRetry.jittered_backoff(retries=10) to retry queries
    with temporary failures.

    Examples:
        tags = paginated_query_with_retries(client, "describe_tags", Filters=[])

        decorator = AWSRetry.backoff(tries=5, delay=5, backoff=2.0,
                                     catch_extra_error_codes=['RequestInProgressException'])
        certificates = paginated_query_with_retries(client, "list_certificates", decorator)
    """
    if retry_decorator is None:
        retry_decorator = AWSRetry.jittered_backoff(retries=10)
    result = retry_decorator(_paginated_query)(client, paginator_name, **params)
    return result


def gather_sdk_versions():
    """Gather AWS SDK (boto3 and botocore) dependency versions

    Returns {'boto3_version': str, 'botocore_version': str}
    Returns {} if either module is not installed
    """
    if not HAS_BOTO3:
        return {}

    return dict(
        boto3_version=boto3.__version__,
        botocore_version=botocore.__version__,
    )


def is_boto3_error_code(code, e=None):
    """Check if the botocore exception is raised by a specific error code.

    Returns ClientError if the error code matches, a dummy exception if it does not have an error code or does not match

    Example:
    try:
        ec2.describe_instances(InstanceIds=['potato'])
    except is_boto3_error_code('InvalidInstanceID.Malformed'):
        # handle the error for that code case
    except botocore.exceptions.ClientError as e:
        # handle the generic error case for all other codes
    """
    from botocore.exceptions import ClientError

    if e is None:
        import sys

        dummy, e, dummy = sys.exc_info()
    if not isinstance(code, (list, tuple, set)):
        code = [code]
    if isinstance(e, ClientError) and e.response["Error"]["Code"] in code:
        return ClientError
    return type("NeverEverRaisedException", (Exception,), {})


def is_boto3_error_message(msg, e=None):
    """Check if the botocore exception contains a specific error message.

    Returns ClientError if the error code matches, a dummy exception if it does not have an error code or does not match

    Example:
    try:
        ec2.describe_vpc_classic_link(VpcIds=[vpc_id])
    except is_boto3_error_message('The functionality you requested is not available in this region.'):
        # handle the error for that error message
    except botocore.exceptions.ClientError as e:
        # handle the generic error case for all other codes
    """
    from botocore.exceptions import ClientError

    if e is None:
        import sys

        dummy, e, dummy = sys.exc_info()
    if isinstance(e, ClientError) and msg in e.response["Error"]["Message"]:
        return ClientError
    return type("NeverEverRaisedException", (Exception,), {})


def get_boto3_client_method_parameters(client, method_name, required=False):
    op = client.meta.method_to_api_mapping.get(method_name)
    input_shape = client._service_model.operation_model(op).input_shape
    if not input_shape:
        parameters = []
    elif required:
        parameters = list(input_shape.required_members)
    else:
        parameters = list(input_shape.members.keys())
    return parameters


# Used by normalize_boto3_result
def _boto3_handler(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    else:
        return obj


def normalize_boto3_result(result):
    """
    Because Boto3 returns datetime objects where it knows things are supposed to
    be dates we need to mass-convert them over to strings which Ansible/Jinja
    handle better.  This also makes it easier to compare complex objects which
    include a mix of dates in string format (from parameters) and dates as
    datetime objects.  Boto3 is happy to be passed ISO8601 format strings.
    """
    return json.loads(json.dumps(result, default=_boto3_handler))


def enable_placebo(session):
    """
    Helper to record or replay offline modules for testing purpose.
    """
    if "_ANSIBLE_PLACEBO_RECORD" in os.environ:
        import placebo

        existing_entries = os.listdir(os.environ["_ANSIBLE_PLACEBO_RECORD"])
        idx = len(existing_entries)
        data_path = f"{os.environ['_ANSIBLE_PLACEBO_RECORD']}/{idx}"
        os.mkdir(data_path)
        pill = placebo.attach(session, data_path=data_path)
        pill.record()
    if "_ANSIBLE_PLACEBO_REPLAY" in os.environ:
        import shutil

        import placebo

        existing_entries = sorted([int(i) for i in os.listdir(os.environ["_ANSIBLE_PLACEBO_REPLAY"])])
        idx = str(existing_entries[0])
        data_path = os.environ["_ANSIBLE_PLACEBO_REPLAY"] + "/" + idx
        try:
            shutil.rmtree("_tmp")
        except FileNotFoundError:
            pass
        shutil.move(data_path, "_tmp")
        if len(existing_entries) == 1:
            os.rmdir(os.environ["_ANSIBLE_PLACEBO_REPLAY"])
        pill = placebo.attach(session, data_path="_tmp")
        pill.playback()


def check_sdk_version_supported(botocore_version=None, boto3_version=None, warn=None):
    """Checks to see if the available boto3 / botocore versions are supported
    args:
        botocore_version: (str) overrides the minimum version of botocore supported by the collection
        boto3_version: (str) overrides the minimum version of boto3 supported by the collection
        warn: (Callable) invoked with a string message if boto3/botocore are less than the
            supported versions
    raises:
        AnsibleBotocoreError - If botocore/boto3 is missing
    returns
        False if boto3 or botocore is less than the minimum supported versions
        True if boto3 and botocore are greater than or equal the the minimum supported versions
    """

    botocore_version = botocore_version or MINIMUM_BOTOCORE_VERSION
    boto3_version = boto3_version or MINIMUM_BOTO3_VERSION

    if not HAS_BOTO3:
        raise AnsibleBotocoreError(message=missing_required_lib("botocore and boto3"))

    supported = True

    if not HAS_PACKAGING:
        if warn:
            warn("packaging.version Python module not installed, unable to check AWS SDK versions")
        return True
    if not botocore_at_least(botocore_version):
        supported = False
        if warn:
            warn(f"botocore < {MINIMUM_BOTOCORE_VERSION} is not supported or tested.  Some features may not work.")
    if not boto3_at_least(boto3_version):
        supported = False
        if warn:
            warn(f"boto3 < {MINIMUM_BOTO3_VERSION} is not supported or tested.  Some features may not work.")

    return supported


def _version_at_least(a, b):
    if not HAS_PACKAGING:
        return True
    return Version(a) >= Version(b)


def boto3_at_least(desired):
    """Check if the available boto3 version is greater than or equal to a desired version.

    Usage:
        if module.params.get('assign_ipv6_address') and not module.boto3_at_least('1.4.4'):
            # conditionally fail on old boto3 versions if a specific feature is not supported
            module.fail_json(msg="Boto3 can't deal with EC2 IPv6 addresses before version 1.4.4.")
    """
    existing = gather_sdk_versions()
    return _version_at_least(existing["boto3_version"], desired)


def botocore_at_least(desired):
    """Check if the available botocore version is greater than or equal to a desired version.

    Usage:
        if not module.botocore_at_least('1.2.3'):
            module.fail_json(msg='The Serverless Elastic Load Compute Service is not in botocore before v1.2.3')
        if not module.botocore_at_least('1.5.3'):
            module.warn('Botocore did not include waiters for Service X before 1.5.3. '
                        'To wait until Service X resources are fully available, update botocore.')
    """
    existing = gather_sdk_versions()
    return _version_at_least(existing["botocore_version"], desired)
