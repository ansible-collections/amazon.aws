# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy

try:
    from botocore.exceptions import WaiterError
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_transit_gateway_vpc_attachment
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_transit_gateway_vpc_attachment
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_subnets
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_transit_gateway_vpc_attachments
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_transit_gateway_vpc_attachment
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.transformation import boto3_resource_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


def get_states() -> List[str]:
    return [
        "available",
        "deleting",
        "failed",
        "failing",
        "initiatingRequest",
        "modifying",
        "pendingAcceptance",
        "pending",
        "rollingBack",
        "rejected",
        "rejecting",
    ]


def subnets_to_vpc(
    client, module: AnsibleAWSModule, subnets: List[str], subnet_details: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    if not subnets:
        return None

    if subnet_details is None:
        try:
            subnet_details = describe_subnets(client, SubnetIds=list(subnets))
        except AnsibleEC2Error as e:
            module.fail_json_aws_error(e)

    vpcs = [s.get("VpcId") for s in subnet_details]
    if len(set(vpcs)) > 1:
        module.fail_json(
            msg="Attachment subnets may only be in one VPC, multiple VPCs found",
            vpcs=list(set(vpcs)),
            subnets=subnet_details,
        )

    return vpcs[0]


def find_existing_attachment(
    client, module: AnsibleAWSModule, filters: Optional[Dict[str, Any]] = None, attachment_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Find an existing transit gateway attachment based on filters or attachment ID.

    Args:
        client: The AWS client used to interact with the EC2 service.
        module: The Ansible module instance used for error handling.
        filters (Optional[Dict[str, Any]]): A dictionary of filters to apply when searching for attachments.
        attachment_id (Optional[str]): The ID of a specific attachment to find.

    Returns:
        Optional[Dict[str, Any]]: The found attachment details or None if not found.

    Raises:
        ValueError: If multiple attachments match the criteria.
    """
    # Find an existing attachment based on filters
    params = {}

    if attachment_id:
        params["TransitGatewayAttachmentIds"] = [attachment_id]
    elif filters:
        params["Filters"] = ansible_dict_to_boto3_filter_list(filters)

    try:
        attachments = describe_transit_gateway_vpc_attachments(client, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    if len(attachments) > 1:
        raise ValueError("Multiple matching attachments found, provide an ID.")

    return attachments[0] if attachments else None


class TransitGatewayAttachmentStateManager:
    def __init__(self, client, module: AnsibleAWSModule, attachment_id: str) -> None:
        self.client = client
        self.module = module
        self.attachment_id = attachment_id

    @property
    def waiter_config(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}

        delay = min(5, self.module.params.get("wait_timeout"))
        max_attempts = self.module.params.get("wait_timeout") // delay
        config = dict(Delay=delay, MaxAttempts=max_attempts)
        params["WaiterConfig"] = config

        return params

    def create_attachment(self, params: Dict[str, Any]) -> str:
        """
        Create a new transit gateway attachment.

        Args:
            params (Dict[str, Any]): A dictionary containing the parameters needed to
                create the transit gateway attachment.

        Returns:
            str: The ID of the newly created transit gateway attachment.

        Raises:
            AnsibleEC2Error: If there is an error while creating the VPC attachment,
                it will fail the module and provide an error message.
        """
        try:
            tags = params.pop("Tags")
        except KeyError:
            tags = None

        if tags:
            params["TagSpecifications"] = boto3_tag_specifications(tags, types=["transit-gateway-attachment"])

        try:
            response = create_transit_gateway_vpc_attachment(self.client, **params)
        except AnsibleEC2Error as e:
            self.module.fail_json_aws_error(e)

        self.attachment_id = response["TransitGatewayAttachmentId"]

        return response["TransitGatewayAttachmentId"]

    def delete_attachment(self) -> bool:
        # Delete the transit gateway attachment

        if not self.attachment_id:
            return False

        if not self.module.check_mode:
            try:
                delete_transit_gateway_vpc_attachment(self.client, self.attachment_id)
            except AnsibleEC2Error as e:
                self.module.fail_json_aws_error(e)

        return True

    def wait_for_state_change(self, desired_state: str) -> None:
        # Wait until attachment reaches the desired state
        params = {"TransitGatewayAttachmentIds": [self.attachment_id]}
        params.update(self.waiter_config)
        waiter = get_waiter(self.client, f"transit_gateway_vpc_attachment_{desired_state}")

        try:
            waiter.wait(**params)
        except WaiterError as e:
            self.module.fail_json_aws(e, "Timeout waiting for State change")


class AttachmentConfigurationManager:
    def __init__(self, client, module: AnsibleAWSModule, attachment_id: str, existing: Dict[str, Any]) -> None:
        self.client = client
        self.module = module
        self.attachment_id = attachment_id

        self.existing = existing or {}
        self._resource_updates = {}
        self._subnets_to_add = []
        self._subnets_to_remove = []

    @property
    def resource_updates(self) -> Dict[str, Any]:
        return self._resource_updates

    @property
    def subnets_to_add(self) -> List[str]:
        return self._subnets_to_add

    @property
    def subnets_to_remove(self) -> List[str]:
        return self._subnets_to_remove

    def set_subnets(self, subnets: Optional[List[str]] = None, purge: bool = True) -> None:
        """
        Set or update the subnets associated with the transit gateway attachment.

        Args:
            subnets (Optional[List[str]]): A list of subnet IDs to associate with
                the attachment.
            purge (bool): If True, the existing subnets will be replaced with the
                specified subnets.
        """
        # Set or update the subnets associated with the attachment
        if subnets is None:
            return

        current_subnets = set(self.existing.get("SubnetIds", []))
        desired_subnets = set(subnets)
        if not purge:
            desired_subnets = desired_subnets.union(current_subnets)

        # We'll pull the VPC ID from the subnets, no point asking for
        # information we 'know'.
        try:
            subnet_details = describe_subnets(self.client, SubnetIds=list(desired_subnets))
        except AnsibleEC2Error as e:
            self.module.fail_json_aws_error(e)
        vpc_id = subnets_to_vpc(self.client, self.module, desired_subnets, subnet_details)
        self._set_resource_value("VpcId", vpc_id, immutable=True)

        # Only one subnet per-AZ is permitted
        azs = [s.get("AvailabilityZoneId") for s in subnet_details]
        if len(azs) != len(set(azs)):
            self.module.fail_json(
                msg="Only one attachment subnet per availability zone may be set.",
                availability_zones=azs,
                subnets=subnet_details,
            )

        self._subnets_to_add = list(desired_subnets.difference(current_subnets))
        self._subnets_to_remove = list(current_subnets.difference(desired_subnets))
        self._set_resource_value("SubnetIds", list(desired_subnets))

    def set_dns_support(self, value):
        return self._set_option("DnsSupport", value)

    def set_ipv6_support(self, value):
        return self._set_option("Ipv6Support", value)

    def set_appliance_mode_support(self, value):
        return self._set_option("ApplianceModeSupport", value)

    def set_transit_gateway(self, tgw_id: str):
        return self._set_resource_value("TransitGatewayId", tgw_id)

    def set_vpc(self, vpc_id: str):
        return self._set_resource_value("VpcId", vpc_id)

    def set_tags(self, tags, purge_tags):
        current_tags = boto3_tag_list_to_ansible_dict(self.existing.get("Tags", None))

        if purge_tags:
            desired_tags = deepcopy(tags)
        else:
            desired_tags = {**current_tags, **tags}

        self._set_resource_value("Tags", desired_tags)

    def _get_resource_value(self, key, default=None):
        default_value = self.existing.get(key, default)
        return self._resource_updates.get(key, default_value)

    def _set_option(self, name: str, value: Optional[bool]) -> bool:
        """
        Set a VPC attachment option to either enable or disable.

        Args:
            name (str): The name of the option to be updated.
            value (Optional[bool]): A boolean indicating whether to enable (True)
                or disable (False) the specified option. If None, no action is
                taken.

        Returns:
            bool: Returns True if the option was successfully set, or False if
            no update was made (because the value was None).
        """
        if value is None:
            return False

        # For now VPC Attachment options are all enable/disable
        value = "enable" if value else "disable"

        options = deepcopy(self.existing.get("Options", dict()))
        options.update(self._resource_updates.get("Options", dict()))
        options[name] = value

        return self._set_resource_value("Options", options)

    def _set_resource_value(self, key, value, description: Optional[str] = None, immutable: bool = False) -> bool:
        """
        Set a value for a resource attribute and track changes.

        Args:
            key (str): The attribute key to be updated.
            value (Any): The new value to set for the specified key.
            description (Optional[str], optional): A human-readable description of the
                resource attribute.
            immutable (bool, optional): A flag indicating whether the attribute is
                immutable. If True, and the resource exists, an error will be raised
                if attempting to change the value. Defaults to False.

        Returns:
            bool: Returns True if the value was successfully set, or False if no
            update was made.
        """
        if value is None or value == self._get_resource_value(key):
            return False

        if immutable and self.existing:
            description = description or key
            self.module.fail_json(msg=f"{description} can not be updated after creation")

        self.resource_updates[key] = value

        return True

    def filter_immutable_resource_attributes(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out immutable resource attributes from the given resource dictionary.

        Args:
            resource (Dict[str, Any]): A dictionary representing the resource, which
                may contain various attributes, including both mutable and immutable ones.

        Returns:
            Dict[str, Any]: A new dictionary containing only the mutable attributes
            of the resource.
        """
        immutable_options = ["TransitGatewayId", "VpcId", "VpcOwnerId", "State", "SubnetIds", "CreationTime", "Tags"]
        return {key: value for key, value in resource.items() if key not in immutable_options}


class TransitGatewayVpcAttachmentManager:
    def __init__(
        self, client, module: AnsibleAWSModule, existing: Dict[str, Any], attachment_id: Optional[str] = None
    ) -> None:
        self.client = client
        self.module = module
        self.attachment_id = attachment_id
        self.existing = existing or {}
        self.updated = {}
        self.changed = False

        self.state_manager = TransitGatewayAttachmentStateManager(client, module, attachment_id)
        self.config_manager = AttachmentConfigurationManager(client, module, attachment_id, existing)

    def merge_resource_changes(self, filter_immutable: bool = True) -> Dict[str, Any]:
        """Merge existing resource attributes with updates, optionally filtering out immutable attributes.

        Args:
            filter_immutable (bool): Whether to filter out immutable resource attributes. Defaults to True.

        Returns:
            Dict[str, Any]: The merged resource attributes.
        """
        resource = deepcopy(self.existing)
        resource.update(self.config_manager.resource_updates)

        if filter_immutable:
            resource = self.config_manager.filter_immutable_resource_attributes(resource)

        return resource

    def apply_configuration(self):
        """Apply configuration changes to the transit gateway attachment.

        Returns:
            bool: True if configuration changes were applied, False otherwise.
        """
        # Apply any configuration changes to the attachment
        if not self.attachment_id:
            return False

        updates = self.config_manager.filter_immutable_resource_attributes(self.config_manager.resource_updates)

        subnets_to_add = self.config_manager.subnets_to_add
        subnets_to_remove = self.config_manager.subnets_to_remove

        # Check if there are no changes to apply
        if not updates and not subnets_to_add and not subnets_to_remove:
            return False

        if subnets_to_add:
            updates["AddSubnetIds"] = subnets_to_add
        if subnets_to_remove:
            updates["RemoveSubnetIds"] = subnets_to_remove

        updates["TransitGatewayAttachmentId"] = self.attachment_id

        if not self.module.check_mode:
            try:
                modify_transit_gateway_vpc_attachment(self.client, **updates)
            except AnsibleEC2Error as e:
                self.module.fail_json_aws_error(e)
        return True

    def _set_configuration_parameters(self) -> None:
        """Set configuration parameters for the transit gateway attachment."""
        self.config_manager.set_transit_gateway(self.module.params.get("transit_gateway"))
        self.config_manager.set_subnets(self.module.params["subnets"], self.module.params.get("purge_subnets", True))
        self.config_manager.set_dns_support(self.module.params.get("dns_support"))
        self.config_manager.set_ipv6_support(self.module.params.get("ipv6_support"))
        self.config_manager.set_appliance_mode_support(self.module.params.get("appliance_mode_support"))

    def _prepare_tags(self) -> Tuple[Optional[Dict[str, str]], bool]:
        """Prepare and return the tags and purge flag.

        Returns:
            Tuple[Optional[Dict[str, str]], bool]: A tuple containing the tags dictionary and the purge flag.
        """
        tags = self.module.params.get("tags")
        purge_tags = self.module.params.get("purge_tags")

        if self.module.params.get("name"):
            new_tags = {"Name": self.module.params["name"]}
            if tags is None:
                purge_tags = False
            else:
                new_tags.update(tags)
            tags = new_tags

        return {} if tags is None else tags, purge_tags

    def _create_attachment(self) -> None:
        """Create a new transit gateway attachment."""
        if not self.module.check_mode:
            params = self.merge_resource_changes(filter_immutable=False)
            self.attachment_id = self.state_manager.create_attachment(params)

            if self.module.params.get("wait"):
                self.state_manager.wait_for_state_change("available")

        self.changed = True

    def _update_attachment(self, tags: Dict[str, Any], purge_tags: bool) -> None:
        """Update an existing transit gateway attachment."""
        if self.existing.get("State") == "pending":
            # Wait for resources to finish creating before updating
            self.state_manager.wait_for_state_change("available")
        elif self.existing.get("State") == "deleting":
            self.module.fail_json(
                msg="Deletion in progress, unable to update",
                attachments=[boto3_resource_to_ansible_dict(self.existing)],
            )

        # Apply the configuration
        if self.apply_configuration():
            self.changed = True
            if self.module.params.get("wait"):
                self.state_manager.wait_for_state_change("available")

        # Ensure tags are applied
        self.changed |= ensure_ec2_tags(
            self.client,
            self.module,
            self.attachment_id,
            resource_type="transit-gateway-attachment",
            tags=tags,
            purge_tags=purge_tags,
        )

    def create_or_modify_attachment(self):
        """Create or modify a transit gateway attachment based on the provided parameters."""

        # Set the configuration parameters
        self._set_configuration_parameters()

        # Handle tags
        tags, purge_tags = self._prepare_tags()

        # Set tags in the configuration manager
        self.config_manager.set_tags(tags, purge_tags)

        if not self.existing:
            self._create_attachment()
        else:
            self._update_attachment(tags, purge_tags)

        # Handle check mode updates
        if self.module.check_mode:
            self.updated = camel_dict_to_snake_dict(
                self.merge_resource_changes(filter_immutable=False), ignore_list=["Tags"]
            )
        else:
            self.updated = boto3_resource_to_ansible_dict(
                find_existing_attachment(self.client, self.module, attachment_id=self.attachment_id)
            )

    def delete_attachment(self):
        """Delete attachment"""
        if self.existing.get("State") == "deleting":
            if self.module.params.get("wait"):
                self.state_manager.wait_for_state_change("deleted")
            self.change = False
        else:
            self.changed |= self.state_manager.delete_attachment()
            if self.module.params.get("wait"):
                self.state_manager.wait_for_state_change("deleted")
