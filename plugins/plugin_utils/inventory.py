# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    import boto3
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible.module_utils._text import to_native
from ansible.template import Templar
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.plugins.inventory import Cacheable
from ansible.plugins.inventory import Constructable
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import boto3_conn
from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase


def _boto3_session(profile_name=None):
    if profile_name is None:
        return boto3.Session()
    return boto3.session.Session(profile_name=profile_name)


class AWSInventoryBase(BaseInventoryPlugin, Constructable, Cacheable, AWSPluginBase):

    def __init__(self):

        super(AWSInventoryBase, self).__init__()

        self.boto_profile = None
        self.aws_secret_access_key = None
        self.aws_access_key_id = None
        self.aws_security_token = None
        self.iam_role_arn = None

    def _get_credentials(self):
        '''
            :return A dictionary of boto client credentials
        '''
        boto_params = {
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key,
            'aws_session_token': self.aws_security_token,
        }
        return {k: v for k, v in boto_params.items() if v}

    def _set_credentials(self, loader):
        '''
            :param config_data: contents of the inventory config file
        '''

        templar = Templar(loader=loader)
        credentials = {}

        for credential_type in ('aws_profile', 'aws_access_key', 'aws_secret_key', 'aws_security_token', 'iam_role_arn'):
            if templar.is_template(self.get_option(credential_type)):
                credentials[credential_type] = templar.template(variable=self.get_option(credential_type), disable_lookups=False)
            else:
                credentials[credential_type] = self.get_option(credential_type)

        self.boto_profile = credentials['aws_profile']
        self.aws_access_key_id = credentials['aws_access_key']
        self.aws_secret_access_key = credentials['aws_secret_key']
        self.aws_security_token = credentials['aws_security_token']
        self.iam_role_arn = credentials['iam_role_arn']

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            session = botocore.session.get_session()
            try:
                credentials = session.get_credentials().get_frozen_credentials()
            except AttributeError:
                pass
            else:
                self.aws_access_key_id = credentials.access_key
                self.aws_secret_access_key = credentials.secret_key
                self.aws_security_token = credentials.token

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            self.fail_aws("Insufficient boto credentials found. Please provide them in your "
                          "inventory configuration file or set them as environment variables.")

    def _get_connection(self, credentials, resource, region='us-east-1'):
        return boto3_conn(self, conn_type='client', resource=resource, region=region, **credentials)

    def _boto3_assume_role(self, credentials, resource, iam_role_arn, profile_name, region=None):
        """
        Assume an IAM role passed by iam_role_arn parameter

        :return: a dict containing the credentials of the assumed role
        """

        try:
            sts_connection = _boto3_session(profile_name=profile_name).client('sts', region, **credentials)
            role_session_name = f"ansible_aws_{resource}_dynamic_inventory"
            sts_session = sts_connection.assume_role(RoleArn=iam_role_arn, RoleSessionName=role_session_name)
            return dict(
                aws_access_key_id=sts_session['Credentials']['AccessKeyId'],
                aws_secret_access_key=sts_session['Credentials']['SecretAccessKey'],
                aws_session_token=sts_session['Credentials']['SessionToken']
            )
        except botocore.exceptions.ClientError as e:
            self.fail_aws("Unable to assume IAM role: %s" % to_native(e))

    def _boto3_regions(self, credentials, iam_role_arn, resource):

        regions = []
        if iam_role_arn is not None:
            try:
                # Describe regions assuming arn role
                assumed_credentials = self._boto3_assume_role(credentials, resource, iam_role_arn, self.boto_profile)
                client = self._get_connection(credentials=assumed_credentials, resource='ec2')
                resp = client.describe_regions()
                regions = [x['RegionName'] for x in resp.get('Regions', [])]
            except botocore.exceptions.NoRegionError:
                # above seems to fail depending on boto3 version, ignore and lets try something else
                pass
        else:
            try:
                # as per https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-regions-avail-zones.html
                client = self._get_connection(credentials=credentials, resource='ec2')
                resp = client.describe_regions()
                regions = [x['RegionName'] for x in resp.get('Regions', [])]
            except botocore.exceptions.NoRegionError:
                # above seems to fail depending on boto3 version, ignore and lets try something else
                pass
            except is_boto3_error_code('UnauthorizedOperation') as e:  # pylint: disable=duplicate-except
                self.fail_aws("Unauthorized operation: %s" % to_native(e))

        # fallback to local list hardcoded in boto3 if still no regions
        if not regions:
            session = _boto3_session()
            regions = session.get_available_regions(resource)

        return regions

    def _get_boto3_connection(self, credentials, iam_role_arn, resource, region):
        try:
            assumed_credentials = credentials
            if iam_role_arn is not None:
                assumed_credentials = self._boto3_assume_role(credentials, resource, iam_role_arn, self.boto_profile, region)
            return _boto3_session(profile_name=self.boto_profile).client(resource, region, **assumed_credentials)
        except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
            if self.boto_profile:
                try:
                    return _boto3_session(profile_name=self.boto_profile).client(resource, region)
                except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                    self.fail_aws("Insufficient credentials found: %s" % to_native(e))
            else:
                self.fail_aws("Insufficient credentials found: %s" % to_native(e))

    def _boto3_conn(self, regions, resource):
        '''
            :param regions: A list of regions to create a boto3 client

            Generator that yields a boto3 client and the region
        '''
        credentials = self._get_credentials()
        iam_role_arn = self.iam_role_arn

        if not regions:
            # list regions as none was provided
            regions = self._boto3_regions(credentials, iam_role_arn, resource)

        # I give up, now you MUST give me regions
        if not regions:
            self.fail_aws('Unable to get regions list from available methods, you must specify the "regions" option to continue.')

        for region in regions:
            connection = self._get_boto3_connection(credentials, iam_role_arn, resource, region)
            yield connection, region
