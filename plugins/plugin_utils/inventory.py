# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import boto3
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.plugins.inventory import Cacheable
from ansible.plugins.inventory import Constructable

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import AnsibleBotocoreError
from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase


def _boto3_session(profile_name=None):
    if profile_name is None:
        return boto3.Session()
    return boto3.session.Session(profile_name=profile_name)


class AWSInventoryBase(BaseInventoryPlugin, Constructable, Cacheable, AWSPluginBase):

    class TemplatedOptions:
        # When someone looks up the TEMPLATABLE_OPTIONS using get() any templates
        # will be templated using the loader passed to parse.
        TEMPLATABLE_OPTIONS = (
            "access_key", "secret_key", "session_token", "profile", "iam_role_name",
        )

        def __init__(self, templar, options):
            self.original_options = options
            self.templar = templar

        def __getitem__(self, *args):
            return self.original_options.__getitem__(self, *args)

        def __setitem__(self, *args):
            return self.original_options.__setitem__(self, *args)

        def get(self, *args):
            value = self.original_options.get(*args)
            if not value:
                return value
            if args[0] not in self.TEMPLATABLE_OPTIONS:
                return value
            if not self.templar.is_template(value):
                return value

            return self.templar.template(variable=value, disable_lookups=False)

    def get_options(self, *args):
        original_options = super().get_options(*args)
        if not self.templar:
            return original_options
        return self.TemplatedOptions(self.templar, original_options)

    def __init__(self):
        super().__init__()
        self._frozen_credentials = {}

    def parse(self, inventory, loader, path, cache=True, botocore_version=None, boto3_version=None):
        super().parse(inventory, loader, path)
        self.require_aws_sdk(botocore_version=botocore_version, boto3_version=boto3_version)
        self._read_config_data(path)
        self._set_frozen_credentials()

    def client(self, *args, **kwargs):
        kw_args = dict(self._frozen_credentials)
        kw_args.update(kwargs)
        return super().client(*args, **kw_args)

    def resource(self, *args, **kwargs):
        kw_args = dict(self._frozen_credentials)
        kw_args.update(kwargs)
        return super().resource(*args, **kw_args)

    def _freeze_iam_role(self, iam_role_arn):
        if hasattr(self, "ansible_name"):
            role_session_name = f"ansible_aws_{self.ansible_name}_dynamic_inventory"
        else:
            role_session_name = "ansible_aws_dynamic_inventory"

        try:
            sts = self.client("sts")
            assumed_role = sts.assume_role(RoleArn=iam_role_arn, RoleSessionName=role_session_name)
        except AnsibleBotocoreError as e:
            self.fail_aws(f"Unable to assume role {iam_role_arn}", exception=e)

        credentials = assumed_role.get("Credentials")
        if not credentials:
            self.fail_aws(f"Unable to assume role {iam_role_arn}")

        self._frozen_credentials = {
            "profile_name": None,
            "aws_access_key_id": credentials.get("AccessKeyId"),
            "aws_secret_access_key": credentials.get("SecretAccessKey"),
            "aws_session_token": credentials.get("SessionToken"),
        }

    def _set_frozen_credentials(self):
        options = self.get_options()
        iam_role_arn = options.get("iam_role_arn")
        if iam_role_arn:
            self._freeze_iam_role(iam_role_arn)

    def _describe_regions(self, service):
        # Try pulling a list of regions from the service
        try:
            client = self.client(service)
            resp = client.describe_regions()
        except AttributeError:
            # Not all clients support describe
            pass
        except is_boto3_error_code("UnauthorizedOperation"):
            self.warn(f"UnauthorizedOperation when trying to list {service} regions")
        except botocore.exceptions.NoRegionError:
            self.warn(f"NoRegionError when trying to list {service} regions")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.warn(f"Unexpected error while trying to list {service} regions: {e}")
        else:
            regions = [x["RegionName"] for x in resp.get("Regions", [])]
            if regions:
                return regions
        return None

    def _boto3_regions(self, service):
        options = self.get_options()

        if options.get("regions"):
            return options.get("regions")

        # boto3 has hard coded lists of available regions for resources, however this does bit-rot
        # As such we try to query the service, and fall back to ec2 for a list of regions
        for resource_type in list({service, "ec2"}):
            regions = self.describe_regions(resource_type)
            if regions:
                return regions

        # fallback to local list hardcoded in boto3 if still no regions
        session = _boto3_session(options.get('profile'))
        regions = session.get_available_regions(service)

        if not regions:
            # I give up, now you MUST give me regions
            self.fail_aws('Unable to get regions list from available methods, you must specify the "regions" option to continue.')

        return regions

    def all_clients(self, service):
        """
            Generator that yields a boto3 client and the region

            :param service: The boto3 service to connect to.

            Note: For services which don't support 'DescribeRegions' this may include bad
            endpoints, and as such EndpointConnectionError should be cleanly handled as a non-fatal
            error.
        """
        regions = self._boto3_regions(service=service)

        for region in regions:
            connection = self.client(service, region=region)
            yield connection, region
