#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: s3_website
version_added: 1.0.0
short_description: Configure an s3 bucket as a website
description:
    - Configure an s3 bucket as a website
requirements: [ boto3 ]
author: Rob White (@wimnat)
options:
  name:
    description:
      - "Name of the s3 bucket"
    required: true
    type: str
  error_key:
    description:
      - "The object key name to use when a 4XX class error occurs. To remove an error key, set to None."
    type: str
  redirect_all_requests:
    description:
      - "Describes the redirect behavior for every request to this s3 bucket website endpoint"
    type: str
  state:
    description:
      - "Add or remove s3 website configuration"
    choices: [ 'present', 'absent' ]
    required: true
    type: str
  suffix:
    description:
      - >
        Suffix that is appended to a request that is for a directory on the website endpoint (e.g. if the suffix is index.html and you make a request to
        samplebucket/images/ the data that is returned will be for the object with the key name images/index.html). The suffix must not include a slash
        character.
    default: index.html
    type: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Configure an s3 bucket to redirect all requests to example.com
  community.aws.s3_website:
    name: mybucket.com
    redirect_all_requests: example.com
    state: present

- name: Remove website configuration from an s3 bucket
  community.aws.s3_website:
    name: mybucket.com
    state: absent

- name: Configure an s3 bucket as a website with index and error pages
  community.aws.s3_website:
    name: mybucket.com
    suffix: home.htm
    error_key: errors/404.htm
    state: present

'''

RETURN = '''
index_document:
    description: index document
    type: complex
    returned: always
    contains:
        suffix:
            description: suffix that is appended to a request that is for a directory on the website endpoint
            returned: success
            type: str
            sample: index.html
error_document:
    description: error document
    type: complex
    returned: always
    contains:
        key:
            description:  object key name to use when a 4XX class error occurs
            returned: when error_document parameter set
            type: str
            sample: error.html
redirect_all_requests_to:
    description: where to redirect requests
    type: complex
    returned: always
    contains:
        host_name:
            description: name of the host where requests will be redirected.
            returned: when redirect all requests parameter set
            type: str
            sample: ansible.com
        protocol:
            description: protocol to use when redirecting requests.
            returned: when redirect all requests parameter set
            type: str
            sample: https
routing_rules:
    description: routing rules
    type: list
    returned: always
    contains:
        condition:
            type: complex
            description: A container for describing a condition that must be met for the specified redirect to apply.
            contains:
                http_error_code_returned_equals:
                    description: The HTTP error code when the redirect is applied.
                    returned: always
                    type: str
                key_prefix_equals:
                    description: object key name prefix when the redirect is applied. For example, to redirect
                                 requests for ExamplePage.html, the key prefix will be ExamplePage.html
                    returned: when routing rule present
                    type: str
                    sample: docs/
        redirect:
            type: complex
            description: Container for redirect information.
            returned: always
            contains:
                host_name:
                    description: name of the host where requests will be redirected.
                    returned: when host name set as part of redirect rule
                    type: str
                    sample: ansible.com
                http_redirect_code:
                    description: The HTTP redirect code to use on the response.
                    returned: when routing rule present
                    type: str
                protocol:
                    description: Protocol to use when redirecting requests.
                    returned: when routing rule present
                    type: str
                    sample: http
                replace_key_prefix_with:
                    description: object key prefix to use in the redirect request
                    returned: when routing rule present
                    type: str
                    sample: documents/
                replace_key_with:
                    description: object key prefix to use in the redirect request
                    returned: when routing rule present
                    type: str
                    sample: documents/
'''

import time

try:
    import boto3
    import botocore
    from botocore.exceptions import ClientError, ParamValidationError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def _create_redirect_dict(url):

    redirect_dict = {}
    url_split = url.split(':')

    # Did we split anything?
    if len(url_split) == 2:
        redirect_dict[u'Protocol'] = url_split[0]
        redirect_dict[u'HostName'] = url_split[1].replace('//', '')
    elif len(url_split) == 1:
        redirect_dict[u'HostName'] = url_split[0]
    else:
        raise ValueError('Redirect URL appears invalid')

    return redirect_dict


def _create_website_configuration(suffix, error_key, redirect_all_requests):

    website_configuration = {}

    if error_key is not None:
        website_configuration['ErrorDocument'] = {'Key': error_key}

    if suffix is not None:
        website_configuration['IndexDocument'] = {'Suffix': suffix}

    if redirect_all_requests is not None:
        website_configuration['RedirectAllRequestsTo'] = _create_redirect_dict(redirect_all_requests)

    return website_configuration


def enable_or_update_bucket_as_website(client_connection, resource_connection, module):

    bucket_name = module.params.get("name")
    redirect_all_requests = module.params.get("redirect_all_requests")
    # If redirect_all_requests is set then don't use the default suffix that has been set
    if redirect_all_requests is not None:
        suffix = None
    else:
        suffix = module.params.get("suffix")
    error_key = module.params.get("error_key")
    changed = False

    try:
        bucket_website = resource_connection.BucketWebsite(bucket_name)
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to get bucket")

    try:
        website_config = client_connection.get_bucket_website(Bucket=bucket_name)
    except is_boto3_error_code('NoSuchWebsiteConfiguration'):
        website_config = None
    except ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get website configuration")

    if website_config is None:
        try:
            bucket_website.put(WebsiteConfiguration=_create_website_configuration(suffix, error_key, redirect_all_requests))
            changed = True
        except (ClientError, ParamValidationError) as e:
            module.fail_json_aws(e, msg="Failed to set bucket website configuration")
        except ValueError as e:
            module.fail_json(msg=str(e))
    else:
        try:
            if (suffix is not None and website_config['IndexDocument']['Suffix'] != suffix) or \
                    (error_key is not None and website_config['ErrorDocument']['Key'] != error_key) or \
                    (redirect_all_requests is not None and website_config['RedirectAllRequestsTo'] != _create_redirect_dict(redirect_all_requests)):

                try:
                    bucket_website.put(WebsiteConfiguration=_create_website_configuration(suffix, error_key, redirect_all_requests))
                    changed = True
                except (ClientError, ParamValidationError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket website configuration")
        except KeyError as e:
            try:
                bucket_website.put(WebsiteConfiguration=_create_website_configuration(suffix, error_key, redirect_all_requests))
                changed = True
            except (ClientError, ParamValidationError) as e:
                module.fail_json(e, msg="Failed to update bucket website configuration")
        except ValueError as e:
            module.fail_json(msg=str(e))

        # Wait 5 secs before getting the website_config again to give it time to update
        time.sleep(5)

    website_config = client_connection.get_bucket_website(Bucket=bucket_name)
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(website_config))


def disable_bucket_as_website(client_connection, module):

    changed = False
    bucket_name = module.params.get("name")

    try:
        client_connection.get_bucket_website(Bucket=bucket_name)
    except is_boto3_error_code('NoSuchWebsiteConfiguration'):
        module.exit_json(changed=changed)
    except ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket website")

    try:
        client_connection.delete_bucket_website(Bucket=bucket_name)
        changed = True
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to delete bucket website")

    module.exit_json(changed=changed)


def main():

    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        suffix=dict(type='str', required=False, default='index.html'),
        error_key=dict(type='str', required=False),
        redirect_all_requests=dict(type='str', required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['redirect_all_requests', 'suffix'],
            ['redirect_all_requests', 'error_key']
        ],
    )

    try:
        client_connection = module.client('s3')
        resource_connection = module.resource('s3')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    state = module.params.get("state")

    if state == 'present':
        enable_or_update_bucket_as_website(client_connection, resource_connection, module)
    elif state == 'absent':
        disable_bucket_as_website(client_connection, module)


if __name__ == '__main__':
    main()
