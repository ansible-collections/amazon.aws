# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import uuid
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.six import string_types

from .ec2 import AnsibleEC2Error
from .ec2 import describe_instances
from .ec2 import describe_subnets
from .ec2 import describe_vpcs
from .ec2 import get_ec2_security_group_ids_from_names
from .modules import AnsibleAWSModule
from .tagging import boto3_tag_specifications
from .tower import tower_callback_script
from .transformation import ansible_dict_to_boto3_filter_list

try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO3


def get_default_vpc(client) -> Optional[Dict[str, Any]]:
    vpcs = describe_vpcs(client, Filters=ansible_dict_to_boto3_filter_list({"isDefault": "true"}))
    return None if len(vpcs) == 0 else vpcs[0]


def get_default_subnet(
    client, vpc: Dict[str, Any], availability_zone: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    subnets = describe_subnets(
        client,
        Filters=ansible_dict_to_boto3_filter_list(
            {
                "vpc-id": vpc["VpcId"],
                "state": "available",
                "default-for-az": "true",
            }
        ),
    )
    if subnets:
        if availability_zone is not None:
            match = [subnet for subnet in subnets if subnet["AvailabilityZone"] == availability_zone]
            if match:
                return match[0]

        # to have a deterministic sorting order, we sort by AZ so we'll always pick the `a` subnet first
        # there can only be one default-for-az subnet per AZ, so the AZ key is always unique in this list
        by_az = sorted(subnets, key=lambda s: s["AvailabilityZone"])
        return by_az[0]
    return None


def discover_security_groups(
    connection, group: Optional[List[str]], groups: Optional[List[str]], parent_vpc_id=None, subnet_id=None
) -> List[Dict[str, Any]]:
    if subnet_id is not None:
        sub = describe_subnets(connection, SubnetIds=[subnet_id])
        if not sub:
            raise AnsibleEC2Error(
                f"Could not find subnet {subnet_id} to associate security groups. Please check the vpc_subnet_id and"
                " security_groups parameters."
            )
        parent_vpc_id = sub[0]["VpcId"]

    if group:
        return get_ec2_security_group_ids_from_names(group, connection, vpc_id=parent_vpc_id)
    if groups:
        return get_ec2_security_group_ids_from_names(groups, connection, vpc_id=parent_vpc_id)
    return []


def build_userdata(params: Dict[str, Any]) -> Dict[str, Any]:
    if params.get("user_data") is not None:
        return {"UserData": to_native(params.get("user_data"))}
    if params.get("aap_callback"):
        userdata = tower_callback_script(
            tower_address=params.get("aap_callback").get("tower_address"),
            job_template_id=params.get("aap_callback").get("job_template_id"),
            host_config_key=params.get("aap_callback").get("host_config_key"),
            windows=params.get("aap_callback").get("windows"),
            passwd=params.get("aap_callback").get("set_password"),
        )
        return {"UserData": userdata}
    return {}


def build_volume_spec(params: Dict[str, Any]) -> Dict[str, Any]:
    volumes = params.get("volumes") or []
    for volume in volumes:
        if "ebs" in volume:
            for int_value in ["volume_size", "iops"]:
                if int_value in volume["ebs"]:
                    volume["ebs"][int_value] = int(volume["ebs"][int_value])
            if "volume_type" in volume["ebs"] and volume["ebs"]["volume_type"] == "gp3":
                if not volume["ebs"].get("iops"):
                    volume["ebs"]["iops"] = 3000
                if "throughput" in volume["ebs"]:
                    volume["ebs"]["throughput"] = int(volume["ebs"]["throughput"])
                else:
                    volume["ebs"]["throughput"] = 125

    return [snake_dict_to_camel_dict(v, capitalize_first=True) for v in volumes]


def build_top_level_options(params: Dict[str, Any]) -> Dict[str, Any]:
    spec = {}
    if params.get("image_id"):
        spec["ImageId"] = params["image_id"]
    elif isinstance(params.get("image"), dict):
        image = params.get("image", {})
        spec["ImageId"] = image.get("id")
        if "ramdisk" in image:
            spec["RamdiskId"] = image["ramdisk"]
        if "kernel" in image:
            spec["KernelId"] = image["kernel"]
    if not spec.get("ImageId") and not params.get("launch_template"):
        raise AnsibleEC2Error(
            "You must include an image_id or image.id parameter to create an instance, or use a launch_template."
        )

    if params.get("key_name") is not None:
        spec["KeyName"] = params.get("key_name")

    spec.update(build_userdata(params))

    if params.get("launch_template") is not None:
        spec["LaunchTemplate"] = {}
        if not params.get("launch_template").get("id") and not params.get("launch_template").get("name"):
            raise AnsibleEC2Error(
                "Could not create instance with launch template. Either launch_template.name or launch_template.id"
                " parameters are required"
            )

        if params.get("launch_template").get("id") is not None:
            spec["LaunchTemplate"]["LaunchTemplateId"] = params.get("launch_template").get("id")
        if params.get("launch_template").get("name") is not None:
            spec["LaunchTemplate"]["LaunchTemplateName"] = params.get("launch_template").get("name")
        if params.get("launch_template").get("version") is not None:
            spec["LaunchTemplate"]["Version"] = to_native(params.get("launch_template").get("version"))

    if params.get("detailed_monitoring", False):
        spec["Monitoring"] = {"Enabled": True}
    if params.get("cpu_credit_specification") is not None:
        spec["CreditSpecification"] = {"CpuCredits": params.get("cpu_credit_specification")}
    if params.get("tenancy") is not None:
        spec["Placement"] = {"Tenancy": params.get("tenancy")}
    if params.get("placement_group"):
        if "Placement" in spec:
            spec["Placement"]["GroupName"] = str(params.get("placement_group"))
        else:
            spec.setdefault("Placement", {"GroupName": str(params.get("placement_group"))})
    if params.get("placement") is not None:
        spec["Placement"] = {}
        if params.get("placement").get("availability_zone") is not None:
            spec["Placement"]["AvailabilityZone"] = params.get("placement").get("availability_zone")
        if params.get("placement").get("affinity") is not None:
            spec["Placement"]["Affinity"] = params.get("placement").get("affinity")
        if params.get("placement").get("group_name") is not None:
            spec["Placement"]["GroupName"] = params.get("placement").get("group_name")
        if params.get("placement").get("host_id") is not None:
            spec["Placement"]["HostId"] = params.get("placement").get("host_id")
        if params.get("placement").get("host_resource_group_arn") is not None:
            spec["Placement"]["HostResourceGroupArn"] = params.get("placement").get("host_resource_group_arn")
        if params.get("placement").get("partition_number") is not None:
            spec["Placement"]["PartitionNumber"] = params.get("placement").get("partition_number")
        if params.get("placement").get("tenancy") is not None:
            spec["Placement"]["Tenancy"] = params.get("placement").get("tenancy")
    if params.get("ebs_optimized") is not None:
        spec["EbsOptimized"] = params.get("ebs_optimized")
    if params.get("instance_initiated_shutdown_behavior"):
        spec["InstanceInitiatedShutdownBehavior"] = params.get("instance_initiated_shutdown_behavior")
    if params.get("termination_protection") is not None:
        spec["DisableApiTermination"] = params.get("termination_protection")
    if params.get("hibernation_options") and params.get("volumes"):
        for vol in params["volumes"]:
            if vol.get("ebs") and vol["ebs"].get("encrypted"):
                spec["HibernationOptions"] = {"Configured": True}
            else:
                raise AnsibleEC2Error(
                    "Hibernation prerequisites not satisfied. Refer to"
                    " https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/hibernating-prerequisites.html"
                )
    if params.get("cpu_options") is not None:
        spec["CpuOptions"] = {}
        spec["CpuOptions"]["ThreadsPerCore"] = params.get("cpu_options").get("threads_per_core")
        spec["CpuOptions"]["CoreCount"] = params.get("cpu_options").get("core_count")
    if params.get("metadata_options"):
        spec["MetadataOptions"] = {}
        spec["MetadataOptions"]["HttpEndpoint"] = params.get("metadata_options").get("http_endpoint")
        spec["MetadataOptions"]["HttpTokens"] = params.get("metadata_options").get("http_tokens")
        spec["MetadataOptions"]["HttpPutResponseHopLimit"] = params.get("metadata_options").get(
            "http_put_response_hop_limit"
        )
        spec["MetadataOptions"]["HttpProtocolIpv6"] = params.get("metadata_options").get("http_protocol_ipv6")
        spec["MetadataOptions"]["InstanceMetadataTags"] = params.get("metadata_options").get("instance_metadata_tags")
    if params.get("additional_info"):
        spec["AdditionalInfo"] = params.get("additional_info")
    if params.get("license_specifications"):
        spec["LicenseSpecifications"] = []
        for license_configuration in params.get("license_specifications"):
            spec["LicenseSpecifications"].append(
                {"LicenseConfigurationArn": license_configuration.get("license_configuration_arn")}
            )
    return spec


def build_network_spec(connection, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns list of interfaces [complex]
    Interface type: {
        'AssociatePublicIpAddress': True|False,
        'DeleteOnTermination': True|False,
        'Description': 'string',
        'DeviceIndex': 123,
        'Groups': [
            'string',
        ],
        'Ipv6AddressCount': 123,
        'Ipv6Addresses': [
            {
                'Ipv6Address': 'string'
            },
        ],
        'NetworkInterfaceId': 'string',
        'PrivateIpAddress': 'string',
        'PrivateIpAddresses': [
            {
                'Primary': True|False,
                'PrivateIpAddress': 'string'
            },
        ],
        'SecondaryPrivateIpAddressCount': 123,
        'SubnetId': 'string'
    },
    """

    interfaces = []
    network = params.get("network") or {}
    spec = dict()
    if not network.get("interfaces"):
        # they only specified one interface
        spec = {
            "DeviceIndex": 0,
        }
        if network.get("assign_public_ip") is not None:
            spec["AssociatePublicIpAddress"] = network["assign_public_ip"]

        if params.get("vpc_subnet_id"):
            spec["SubnetId"] = params["vpc_subnet_id"]
        else:
            default_vpc = get_default_vpc(connection)
            if default_vpc is None:
                raise AnsibleEC2Error(
                    "No default subnet could be found - you must include a VPC subnet ID (vpc_subnet_id parameter)"
                    " to create an instance"
                )
            sub = get_default_subnet(connection, vpc=default_vpc, availability_zone=params.get("availability_zone"))
            spec["SubnetId"] = (sub or {}).get("SubnetId")

        if network.get("private_ip_address"):
            spec["PrivateIpAddress"] = network["private_ip_address"]

        if params.get("security_group") or params.get("security_groups"):
            group = params.get("security_group")
            groups = params.get("security_groups")
            groups = discover_security_groups(connection, group, groups, subnet_id=spec["SubnetId"])
            spec["Groups"] = groups
        if network.get("description") is not None:
            spec["Description"] = network["description"]
        # TODO more special snowflake network things

        return [spec]

    # handle list of `network.interfaces` options
    for idx, interface_params in enumerate(network.get("interfaces", [])):
        spec = {
            "DeviceIndex": idx,
        }

        if isinstance(interface_params, string_types):
            # naive case where user gave
            # network_interfaces: [eni-1234, eni-4567, ....]
            # put into normal data structure so we don't dupe code
            interface_params = {"id": interface_params}

        if interface_params.get("id") is not None:
            # if an ID is provided, we don't want to set any other parameters.
            spec["NetworkInterfaceId"] = interface_params["id"]
            interfaces.append(spec)
            continue

        spec["DeleteOnTermination"] = interface_params.get("delete_on_termination", True)

        if interface_params.get("ipv6_addresses"):
            spec["Ipv6Addresses"] = [{"Ipv6Address": a} for a in interface_params.get("ipv6_addresses", [])]

        if interface_params.get("private_ip_address"):
            spec["PrivateIpAddress"] = interface_params.get("private_ip_address")

        if interface_params.get("description"):
            spec["Description"] = interface_params.get("description")

        if interface_params.get("subnet_id", params.get("vpc_subnet_id")):
            spec["SubnetId"] = interface_params.get("subnet_id", params.get("vpc_subnet_id"))
        elif not spec.get("SubnetId") and not interface_params["id"]:
            # TODO grab a subnet from default VPC
            raise ValueError(f"Failed to assign subnet to interface {interface_params}")

        interfaces.append(spec)
    return interfaces


def build_run_instance_spec(connection, params: Dict[str, Any], current_count=0, iam_role_arn=None) -> Dict[str, Any]:
    spec = dict(
        ClientToken=uuid.uuid4().hex,
        MaxCount=1,
        MinCount=1,
    )
    spec.update(**build_top_level_options(params))

    spec["NetworkInterfaces"] = build_network_spec(connection, params)
    spec["BlockDeviceMappings"] = build_volume_spec(params)

    tag_spec = build_instance_tags(params)
    if tag_spec is not None:
        spec["TagSpecifications"] = tag_spec

    # IAM profile
    if iam_role_arn:
        spec["IamInstanceProfile"] = {"Arn": iam_role_arn}

    if params.get("exact_count"):
        spec["MaxCount"] = params.get("exact_count") - current_count
        spec["MinCount"] = params.get("exact_count") - current_count

    if params.get("count"):
        spec["MaxCount"] = params.get("count")
        spec["MinCount"] = params.get("count")

    if params.get("instance_type"):
        spec["InstanceType"] = params["instance_type"]

    if not (params.get("instance_type") or params.get("launch_template")):
        raise AnsibleEC2Error(
            "At least one of 'instance_type' and 'launch_template' must be passed when launching instances."
        )

    return spec


def build_instance_tags(params: Dict[str, Any]) -> Dict[str, str]:
    tags = params.get("tags") or {}
    if params.get("name") is not None:
        tags["Name"] = params.get("name")
    specs = boto3_tag_specifications(tags, ["volume", "instance"])
    return specs


# EC2 instances modules utilities
class EC2InstanceModule(AnsibleAWSModule):
    _ANSIBLE_STATE_TO_EC2_MAPPING = {
        "present": {"waiter": "instance_exists", "state": "running"},
        "started": {"waiter": "instance_status_ok", "state": "running"},
        "running": {"waiter": "instance_running", "state": "running"},
        "stopped": {"waiter": "instance_stopped", "state": "stopped"},
        "restarted": {"waiter": "instance_status_ok", "state": "running"},
        "rebooted": {"waiter": "instance_running", "state": "running"},
        "terminated": {"waiter": "instance_terminated", "state": "terminated"},
        "absent": {"waiter": "instance_terminated", "state": "terminated"},
    }

    def __init__(self) -> None:
        super().__init__(
            argument_spec=self.argument_specs(),
            mutually_exclusive=[
                ["security_groups", "security_group"],
                ["availability_zone", "vpc_subnet_id"],
                ["aap_callback", "user_data"],
                ["image_id", "image"],
                ["exact_count", "count"],
                ["exact_count", "instance_ids"],
                ["tenancy", "placement"],
                ["placement_group", "placement"],
            ],
            supports_check_mode=True,
        )

        if self.params.get("network"):
            if self.params.get("network").get("interfaces"):
                if self.params.get("security_group"):
                    self.fail_json(msg="Parameter network.interfaces can't be used with security_group")
                if self.params.get("security_groups"):
                    self.fail_json(msg="Parameter network.interfaces can't be used with security_groups")

        if self.params.get("placement_group"):
            self.deprecate(
                "The placement_group parameter has been deprecated, please use placement.group_name instead.",
                date="2025-12-01",
                collection_name="amazon.aws",
            )

        if self.params.get("tenancy"):
            self.deprecate(
                "The tenancy parameter has been deprecated, please use placement.tenancy instead.",
                date="2025-12-01",
                collection_name="amazon.aws",
            )

        self.ec2_client = self.client("ec2")

    @property
    def ec2(self):
        return self.ec2_client

    @staticmethod
    def argument_specs() -> Dict[str, Any]:
        # running/present are synonyms
        # as are terminated/absent
        return dict(
            state=dict(
                default="present",
                choices=["present", "started", "running", "stopped", "restarted", "rebooted", "terminated", "absent"],
            ),
            wait=dict(default=True, type="bool"),
            wait_timeout=dict(default=600, type="int"),
            count=dict(type="int"),
            exact_count=dict(type="int"),
            image=dict(type="dict"),
            image_id=dict(type="str"),
            instance_type=dict(type="str"),
            user_data=dict(type="str"),
            aap_callback=dict(
                type="dict",
                aliases=["tower_callback"],
                required_if=[
                    (
                        "windows",
                        False,
                        (
                            "tower_address",
                            "job_template_id",
                            "host_config_key",
                        ),
                        False,
                    ),
                ],
                options=dict(
                    windows=dict(type="bool", default=False),
                    set_password=dict(type="str", no_log=True),
                    tower_address=dict(type="str"),
                    job_template_id=dict(type="str"),
                    host_config_key=dict(type="str", no_log=True),
                ),
            ),
            ebs_optimized=dict(type="bool"),
            vpc_subnet_id=dict(type="str", aliases=["subnet_id"]),
            availability_zone=dict(type="str"),
            security_groups=dict(default=[], type="list", elements="str"),
            security_group=dict(type="str"),
            iam_instance_profile=dict(type="str", aliases=["instance_role"]),
            name=dict(type="str"),
            tags=dict(type="dict", aliases=["resource_tags"]),
            purge_tags=dict(type="bool", default=True),
            filters=dict(type="dict", default=None),
            launch_template=dict(type="dict"),
            license_specifications=dict(
                type="list",
                elements="dict",
                options=dict(
                    license_configuration_arn=dict(type="str", required=True),
                ),
            ),
            key_name=dict(type="str"),
            cpu_credit_specification=dict(type="str", choices=["standard", "unlimited"]),
            cpu_options=dict(
                type="dict",
                options=dict(
                    core_count=dict(type="int", required=True),
                    threads_per_core=dict(type="int", choices=[1, 2], required=True),
                ),
            ),
            tenancy=dict(type="str", choices=["dedicated", "default"]),
            placement_group=dict(type="str"),
            placement=dict(
                type="dict",
                options=dict(
                    affinity=dict(type="str"),
                    availability_zone=dict(type="str"),
                    group_name=dict(type="str"),
                    host_id=dict(type="str"),
                    host_resource_group_arn=dict(type="str"),
                    partition_number=dict(type="int"),
                    tenancy=dict(type="str", choices=["dedicated", "default", "host"]),
                ),
            ),
            instance_initiated_shutdown_behavior=dict(type="str", choices=["stop", "terminate"]),
            termination_protection=dict(type="bool"),
            hibernation_options=dict(type="bool", default=False),
            detailed_monitoring=dict(type="bool"),
            instance_ids=dict(default=[], type="list", elements="str"),
            network=dict(default=None, type="dict"),
            volumes=dict(default=None, type="list", elements="dict"),
            metadata_options=dict(
                type="dict",
                options=dict(
                    http_endpoint=dict(choices=["enabled", "disabled"], default="enabled"),
                    http_put_response_hop_limit=dict(type="int", default=1),
                    http_tokens=dict(choices=["optional", "required"], default="optional"),
                    http_protocol_ipv6=dict(choices=["disabled", "enabled"], default="disabled"),
                    instance_metadata_tags=dict(choices=["disabled", "enabled"], default="disabled"),
                ),
            ),
            additional_info=dict(type="str"),
        )

    def get_default_vpc(self) -> Optional[Dict[str, Any]]:
        return get_default_vpc(self.ec2)

    def get_default_subnet(
        self, vpc: Dict[str, Any], availability_zone: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        return get_default_subnet(self.ec2, vpc=vpc, availability_zone=availability_zone)

    def build_filters(self) -> Dict[str, Any]:
        filters = {
            # all states except shutting-down and terminated
            "instance-state-name": ["pending", "running", "stopping", "stopped"],
        }
        instance_ids = self.params.get("instance_ids")
        if isinstance(instance_ids, string_types):
            filters["instance-id"] = [instance_ids]
        elif isinstance(instance_ids, list) and len(instance_ids) > 0:
            filters["instance-id"] = instance_ids
        else:
            vpc_subnet_id = self.params.get("vpc_subnet_id")
            if not vpc_subnet_id:
                network = self.params.get("network")
                if network:
                    # grab AZ from one of the ENIs
                    interfaces = network.get("interfaces")
                    if interfaces:
                        filters["network-interface.network-interface-id"] = []
                        for i in interfaces:
                            if isinstance(i, dict):
                                i = i["id"]
                            filters["network-interface.network-interface-id"].append(i)
                else:
                    default_vpc = self.get_default_vpc()
                    if default_vpc is None:
                        raise AnsibleEC2Error(
                            "No default subnet could be found - you must include a VPC subnet ID (vpc_subnet_id parameter)"
                            " to create an instance"
                        )
                    sub = self.get_default_subnet(default_vpc, availability_zone=self.params.get("availability_zone"))
                    filters["subnet-id"] = sub.get("SubnetId")
            else:
                filters["subnet-id"] = [vpc_subnet_id]

            name = self.params.get("name")
            tags = self.params.get("tags")
            if name:
                filters["tag:Name"] = [name]
            elif tags:
                name_tag = tags.get("Name")
                if name_tag:
                    filters["tag:Name"] = [name_tag]

            image_id = self.params.get("image_id")
            image = self.params.get("image")
            if image_id:
                filters["image-id"] = [image_id]
            elif image and image.get("id"):
                filters["image-id"] = [image.get("id")]
        return filters

    def find_instances(
        self, ids: Optional[List[str]] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        sanitized_filters = dict()
        if ids:
            params = {"InstanceIds": ids}
        elif filters is None:
            self.fail_json(msg="No filters provided when they were required")
        else:
            for key in list((filters or {}).keys()):
                if not key.startswith("tag:"):
                    sanitized_filters[key.replace("_", "-")] = (filters or {}).get(key)
                else:
                    sanitized_filters[key] = (filters or {}).get(key)
            params = {"Filters": ansible_dict_to_boto3_filter_list(sanitized_filters)}

        results = []
        for reservation in describe_instances(self.ec2, **params):
            results += reservation.get("Instances", [])
        return results

    def await_instances(self, ids: List[str], desired_module_state: str = "present", force_wait: bool = False) -> None:
        if not self.check_mode and ids and (self.params.get("wait", True) or force_wait):
            boto3_waiter_type = self._ANSIBLE_STATE_TO_EC2_MAPPING.get(desired_module_state, {}).get("waiter")
            if not boto3_waiter_type:
                self.fail_json(msg=f"Cannot wait for state {desired_module_state}, invalid state")
            waiter = self.ec2.get_waiter(boto3_waiter_type)
            try:
                waiter.wait(
                    InstanceIds=ids,
                    WaiterConfig={
                        "Delay": 15,
                        "MaxAttempts": self.params.get("wait_timeout", 600) // 15,
                    },
                )
            except botocore.exceptions.WaiterConfigError as e:
                instance_ids = ", ".join(ids)
                self.fail_json(
                    msg=f"{to_native(e)}. Error waiting for instances {instance_ids} to reach state {boto3_waiter_type}"
                )
            except botocore.exceptions.WaiterError as e:
                instance_ids = ", ".join(ids)
                self.warn(f"Instances {instance_ids} took too long to reach state {boto3_waiter_type}. {to_native(e)}")

    def _update_instances(self, operation: str, instance_ids: List[str]) -> Tuple[List[str], str]:
        _OPERATION_MAPPING = {
            "terminate": "TerminatingInstances",
            "stop": "StoppingInstances",
            "start": "StartingInstances",
        }

        failure_reason = ""
        result_instance_ids = []
        try:
            func = getattr(self.ec2, operation + "_instances")
            result = func(InstanceIds=instance_ids)
            result_instance_ids = [i["InstanceId"] for i in result[_OPERATION_MAPPING.get(operation)]]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            try:
                failure_reason = to_native(e.message)
            except AttributeError:
                failure_reason = to_native(e)
        return result_instance_ids, failure_reason

    def _terminate_ec2_instances(self, instances: List[Dict[str, Any]]) -> Tuple[List[str], List[str], str]:
        # Before terminating an instance we need for them to leave
        # 'pending' or 'stopping' (if they're in those states)
        wait_status_stopped = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] == "stopping"
        ]
        wait_status_running = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] == "pending"
        ]

        self.await_instances(ids=wait_status_stopped, desired_module_state="stopped", force_wait=True)
        self.await_instances(ids=wait_status_running, desired_module_state="running", force_wait=True)

        # now terminate instances as they have reached the expected status
        terminated_instance_ids = [instance["InstanceId"] for instance in instances]
        failure_reason = ""
        if not self.check_mode and terminated_instance_ids:
            terminated_instance_ids, failure_reason = self._update_instances(
                operation="terminate", instance_ids=terminated_instance_ids
            )
        return terminated_instance_ids, [], failure_reason

    def _stop_ec2_instances(self, instances: List[Dict[str, Any]]) -> Tuple[List[str], List[str], str]:
        # Before stopping an instance we need for them to leave 'pending'
        wait_status_running = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] == "pending"
        ]
        self.await_instances(ids=wait_status_running, desired_module_state="running", force_wait=True)

        # Instances already moving to the relevant state
        already_stopped_instances = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] in ("stopping", "stopped")
        ]

        # now stop instances as they have reached the expected status
        stopped_instance_ids = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] not in ("stopping", "stopped")
        ]
        failure_reason = ""
        if not self.check_mode and stopped_instance_ids:
            stopped_instance_ids, failure_reason = self._update_instances(
                operation="stop", instance_ids=stopped_instance_ids
            )

        return stopped_instance_ids, already_stopped_instances, failure_reason

    def _start_ec2_instances(self, instances: List[Dict[str, Any]]) -> Tuple[List[str], List[str], str]:
        # Before stopping an instance we need for them to leave 'pending'
        wait_status_stopped = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] == "stopping"
        ]
        self.await_instances(ids=wait_status_stopped, desired_module_state="stopped", force_wait=True)

        # Instances already moving to the relevant state
        already_running_instances = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] in ("pending", "running")
        ]

        # Now start instances as they have reached the expected status
        started_instance_ids = [
            instance["InstanceId"] for instance in instances if instance["State"]["Name"] not in ("pending", "running")
        ]
        failure_reason = ""
        if not self.check_mode and started_instance_ids:
            started_instance_ids, failure_reason = self._update_instances(
                operation="start", instance_ids=started_instance_ids
            )
        return started_instance_ids, already_running_instances, failure_reason

    def change_instance_state(
        self, filters: Optional[List[Dict[str, Any]]], desired_module_state: str
    ) -> Tuple[List[str], List[str], List[Dict[str, Any]], str]:
        desired_ec2_state = self._ANSIBLE_STATE_TO_EC2_MAPPING[desired_module_state].get("state")
        instances = self.find_instances(filters=filters)
        changed = []
        change_failed = []
        failure_reason = ""
        if instances:
            to_change = set(
                instance["InstanceId"] for instance in instances if instance["State"]["Name"] != desired_ec2_state
            )

            if desired_ec2_state == "terminated":
                changed, unchanged, failure_reason = self._terminate_ec2_instances(instances)
            elif desired_ec2_state == "stopped":
                changed, unchanged, failure_reason = self._stop_ec2_instances(instances)
            elif desired_ec2_state == "running":
                changed, unchanged, failure_reason = self._start_ec2_instances(instances)

            if changed:
                self.await_instances(ids=changed + unchanged, desired_module_state=desired_module_state)

            change_failed = list(to_change - set(changed))
            changed = list(set(changed))
            instances = self.find_instances(ids=[i["InstanceId"] for i in instances])
        return changed, change_failed, instances, failure_reason
