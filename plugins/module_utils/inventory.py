# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    import boto3
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3
from abc import ABCMeta, abstractmethod

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible.module_utils._text import to_native


class AWSInventoryFailure(Exception):
    pass


class AnsibleAWSInventory(metaclass=ABCMeta):

    def __init__(self):

        self.boto_profile = None
        self.aws_secret_access_key = None
        self.aws_access_key_id = None
        self.aws_security_token = None
        self.iam_role_arn = None

    @abstractmethod
    def get_option(self, option, hostvars=None):
        pass

    def _get_credentials(self):
        '''
            :return A dictionary of boto client credentials
        '''
        boto_params = {}
        for credential in (('aws_access_key_id', self.aws_access_key_id),
                           ('aws_secret_access_key', self.aws_secret_access_key),
                           ('aws_session_token', self.aws_security_token)):
            if credential[1]:
                boto_params[credential[0]] = credential[1]

        return boto_params

    def _set_credentials(self, templar):
        '''
            :param config_data: contents of the inventory config file
        '''

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
            raise AWSInventoryFailure("Insufficient boto credentials found. Please provide them in your "
                                      "inventory configuration file or set them as environment variables.")

    def _boto3_assume_role(self, credentials, service, region=None):
        """
        Assume an IAM role passed by iam_role_arn parameter

        :return: a dict containing the credentials of the assumed role
        """

        iam_role_arn = self.iam_role_arn

        try:
            sts_connection = boto3.session.Session(profile_name=self.boto_profile).client('sts', region, **credentials)
            role_session_name = f"ansible_aws_{service}_dynamic_inventory"
            sts_session = sts_connection.assume_role(RoleArn=iam_role_arn, RoleSessionName=role_session_name)
            return dict(
                aws_access_key_id=sts_session['Credentials']['AccessKeyId'],
                aws_secret_access_key=sts_session['Credentials']['SecretAccessKey'],
                aws_session_token=sts_session['Credentials']['SessionToken']
            )
        except botocore.exceptions.ClientError as e:
            raise AWSInventoryFailure("Unable to assume IAM role: %s" % to_native(e))

    def _get_connection(self, credentials, service, region='us-east-1'):
        try:
            connection = boto3.session.Session(profile_name=self.boto_profile).client(service, region, **credentials)
        except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
            if self.boto_profile:
                try:
                    connection = boto3.session.Session(profile_name=self.boto_profile).client(service, region)
                except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                    raise AWSInventoryFailure("Insufficient credentials found: %s" % to_native(e))
            else:
                raise AWSInventoryFailure("Insufficient credentials found: %s" % to_native(e))
        return connection

    def _boto3_conn(self, regions, service):
        '''
            :param regions: A list of regions to create a boto3 client

            Generator that yields a boto3 client and the region
        '''

        credentials = self._get_credentials()
        iam_role_arn = self.iam_role_arn

        if not regions:
            try:
                # as per https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-regions-avail-zones.html
                client = self._get_connection(credentials, service)
                resp = client.describe_regions()
                regions = [x['RegionName'] for x in resp.get('Regions', [])]
            except botocore.exceptions.NoRegionError:
                # above seems to fail depending on boto3 version, ignore and lets try something else
                pass
            except is_boto3_error_code('UnauthorizedOperation') as e:  # pylint: disable=duplicate-except
                if iam_role_arn is not None:
                    try:
                        # Describe regions assuming arn role
                        assumed_credentials = self._boto3_assume_role(credentials, service)
                        client = self._get_connection(assumed_credentials, service)
                        resp = client.describe_regions()
                        regions = [x['RegionName'] for x in resp.get('Regions', [])]
                    except botocore.exceptions.NoRegionError:
                        # above seems to fail depending on boto3 version, ignore and lets try something else
                        pass
                else:
                    raise AWSInventoryFailure("Unauthorized operation: %s" % to_native(e))

        # fallback to local list hardcoded in boto3 if still no regions
        if not regions:
            session = boto3.Session()
            regions = session.get_available_regions(service)

        # I give up, now you MUST give me regions
        if not regions:
            raise AWSInventoryFailure('Unable to get regions list from available methods, you must specify the "regions" option to continue.')

        for region in regions:
            connection = self._get_connection(credentials, service, region)
            try:
                if iam_role_arn is not None:
                    assumed_credentials = self._boto3_assume_role(credentials, service, region)
                else:
                    assumed_credentials = credentials
                connection = boto3.session.Session(profile_name=self.boto_profile).client(service, region, **assumed_credentials)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                if self.boto_profile:
                    try:
                        connection = boto3.session.Session(profile_name=self.boto_profile).client(service, region)
                    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                        raise AWSInventoryFailure("Insufficient credentials found: %s" % to_native(e))
                else:
                    raise AWSInventoryFailure("Insufficient credentials found: %s" % to_native(e))
            yield connection, region
