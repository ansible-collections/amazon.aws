# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import boto3
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.plugins.inventory import Cacheable
from ansible.plugins.inventory import Constructable

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import AnsibleBotocoreError


def _boto3_session(profile_name=None):
    if profile_name is None:
        return boto3.Session()
    return boto3.session.Session(profile_name=profile_name)


class AWSInventoryBase(BaseInventoryPlugin, Constructable, Cacheable, AWSPluginBase):
    class TemplatedOptions:
        # When someone looks up the TEMPLATABLE_OPTIONS using get() any templates
        # will be templated using the loader passed to parse.
        TEMPLATABLE_OPTIONS = (
            "access_key",
            "secret_key",
            "session_token",
            "profile",
            "endpoint_url",
            "assume_role_arn",
            "region",
            "regions",
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
            if (
                not value
                or not self.templar
                or args[0] not in self.TEMPLATABLE_OPTIONS
                or not self.templar.is_template(value)
            ):
                return value

            return self.templar.template(variable=value, disable_lookups=False)

    def get_options(self, *args):
        return self.TemplatedOptions(self.templar, super().get_options(*args))

    def get_option(self, option, hostvars=None):
        return self.TemplatedOptions(self.templar, {option: super().get_option(option, hostvars)}).get(option)

    def __init__(self):
        super().__init__()
        self._frozen_credentials = {}

    # pylint: disable=too-many-arguments
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
        assume_params = {"RoleArn": iam_role_arn, "RoleSessionName": role_session_name}

        try:
            sts = self.client("sts")
            assumed_role = sts.assume_role(**assume_params)
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
        iam_role_arn = self.get_option("assume_role_arn")
        if iam_role_arn:
            self._freeze_iam_role(iam_role_arn)

    def _describe_regions(self, service):
        # Try pulling a list of regions from the service
        try:
            initial_region = self.region or "us-east-1"
            client = self.client(service, region=initial_region)
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
        regions = self.get_option("regions")
        if regions:
            return regions

        # boto3 has hard coded lists of available regions for resources, however this does bit-rot
        # As such we try to query the service, and fall back to ec2 for a list of regions
        for resource_type in list({service, "ec2"}):
            regions = self._describe_regions(resource_type)
            if regions:
                return regions

        # fallback to local list hardcoded in boto3 if still no regions
        session = _boto3_session(self.get_option("profile"))
        regions = session.get_available_regions(service)

        if not regions:
            # I give up, now you MUST give me regions
            self.fail_aws(
                "Unable to get regions list from available methods, you must specify the 'regions' option to continue."
            )

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

    def get_cached_result(self, path, cache):
        # false when refresh_cache or --flush-cache is used
        if not cache:
            return False, None
        # get the user-specified directive
        if not self.get_option("cache"):
            return False, None

        cache_key = self.get_cache_key(path)
        try:
            cached_value = self._cache[cache_key]
        except KeyError:
            # if cache expires or cache file doesn"t exist
            return False, None

        return True, cached_value

    def update_cached_result(self, path, cache, result):
        if not self.get_option("cache"):
            return

        cache_key = self.get_cache_key(path)
        # We weren't explicitly told to flush the cache, and there's already a cache entry,
        # this means that the result we're being passed came from the cache.  As such we don't
        # want to "update" the cache as that could reset a TTL on the cache entry.
        if cache and cache_key in self._cache:
            return

        self._cache[cache_key] = result

    def verify_file(self, path):
        """
        :param path: the path to the inventory config file
        :return the contents of the config file
        """
        if not super().verify_file(path):
            return False

        if hasattr(self, "INVENTORY_FILE_SUFFIXES"):
            if not path.endswith(self.INVENTORY_FILE_SUFFIXES):
                return False

        return True
