#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_launch_config
version_added: 1.0.0

short_description: Create or delete AWS Autoscaling Launch Configurations

description:
  - Can create or delete AWS Autoscaling Configurations.
  - Works with the M(community.aws.autoscaling_group) module to manage Autoscaling Groups.
  - Prior to release 5.0.0 this module was called C(community.aws.ec2_lc).
    The usage did not change.

notes:
  - Amazon ASG Autoscaling Launch Configurations are immutable once created, so modifying the configuration after it is changed will not modify the
    launch configuration on AWS. You must create a new config and assign it to the ASG instead.

author:
  - "Gareth Rushgrove (@garethr)"
  - "Willem van Ketwich (@wilvk)"

options:
  state:
    description:
      - Register or deregister the instance.
    default: present
    choices: ['present', 'absent']
    type: str
  name:
    description:
      - Unique name for configuration.
    required: true
    type: str
  instance_type:
    description:
      - Instance type to use for the instance.
      - Required when creating a new Launch Configuration.
    type: str
  image_id:
    description:
      - The AMI unique identifier to be used for the group.
    type: str
  key_name:
    description:
      - The SSH key name to be used for access to managed instances.
    type: str
  security_groups:
    description:
      - A list of security groups to apply to the instances.
      - You can specify either security group names or IDs or a mix.
    type: list
    elements: str
    default: []
  volumes:
    description:
      - A list dictionaries defining the volumes to create.
      - For any volume, a volume size less than C(1) will be interpreted as a request not to create the volume.
    type: list
    elements: dict
    suboptions:
      device_name:
        type: str
        description:
          - The name for the volume (For example C(/dev/sda)).
        required: true
      no_device:
        type: bool
        description:
          - When I(no_device=true) the device will not be created.
      snapshot:
        type: str
        description:
          - The ID of an EBS snapshot to copy when creating the volume.
          - Mutually exclusive with the I(ephemeral) parameter.
      ephemeral:
        type: str
        description:
          - Whether the volume should be ephemeral.
          - Data on ephemeral volumes is lost when the instance is stopped.
          - Mutually exclusive with the I(snapshot) parameter.
      volume_size:
        type: int
        description:
          - The size of the volume (in GiB).
          - Required unless one of I(ephemeral), I(snapshot) or I(no_device) is set.
      volume_type:
        type: str
        description:
          - The type of volume to create.
          - See
            U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumeTypes.html) for more information on the available volume types.
      delete_on_termination:
        type: bool
        default: false
        description:
          - Whether the volume should be automatically deleted when the instance
            is terminated.
      iops:
        type: int
        description:
          - The number of IOPS per second to provision for the volume.
          - Required when I(volume_type=io1).
      throughput:
        type: int
        description:
          - The throughput to provision for a gp3 volume.
          - Valid Range is a minimum value of 125 and a maximum value of 1000.
        version_added: 3.1.0
      encrypted:
        type: bool
        default: false
        description:
          - Whether the volume should be encrypted using the 'aws/ebs' KMS CMK.
  user_data:
    description:
      - Opaque blob of data which is made available to the ec2 instance. Mutually exclusive with I(user_data_path).
    type: str
  user_data_path:
    description:
      - Path to the file that contains userdata for the ec2 instances. Mutually exclusive with I(user_data).
    type: path
  kernel_id:
    description:
      - Kernel id for the EC2 instance.
    type: str
  spot_price:
    description:
      - The spot price you are bidding. Only applies for an autoscaling group with spot instances.
    type: float
  instance_monitoring:
    description:
      - Specifies whether instances are launched with detailed monitoring.
    type: bool
    default: false
  assign_public_ip:
    description:
      - Used for Auto Scaling groups that launch instances into an Amazon Virtual Private Cloud. Specifies whether to assign a public IP address
        to each instance launched in a Amazon VPC.
    type: bool
  ramdisk_id:
    description:
      - A RAM disk id for the instances.
    type: str
  instance_profile_name:
    description:
      - The name or the Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instances.
    type: str
  ebs_optimized:
    description:
      - Specifies whether the instance is optimized for EBS I/O (true) or not (false).
    default: false
    type: bool
  classic_link_vpc_id:
    description:
      - Id of ClassicLink enabled VPC
    type: str
  classic_link_vpc_security_groups:
    description:
      - A list of security group IDs with which to associate the ClassicLink VPC instances.
    type: list
    elements: str
  vpc_id:
    description:
      - VPC ID, used when resolving security group names to IDs.
    type: str
  instance_id:
    description:
      - The Id of a running instance to use as a basis for a launch configuration. Can be used in place of I(image_id) and I(instance_type).
    type: str
  placement_tenancy:
    description:
      - Determines whether the instance runs on single-tenant hardware or not.
      - When not set AWS will default to C(default).
    type: str
    choices: ['default', 'dedicated']
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""

- name: create a launch configuration with an encrypted volume
  community.aws.autoscaling_launch_config:
    name: special
    image_id: ami-XXX
    key_name: default
    security_groups: ['group', 'group2' ]
    instance_type: t1.micro
    volumes:
    - device_name: /dev/sda1
      volume_size: 100
      volume_type: io1
      iops: 3000
      delete_on_termination: true
      encrypted: true
    - device_name: /dev/sdb
      ephemeral: ephemeral0

- name: create a launch configuration using a running instance id as a basis
  community.aws.autoscaling_launch_config:
    name: special
    instance_id: i-00a48b207ec59e948
    key_name: default
    security_groups: ['launch-wizard-2' ]
    volumes:
    - device_name: /dev/sda1
      volume_size: 120
      volume_type: io1
      iops: 3000
      delete_on_termination: true

- name: create a launch configuration to omit the /dev/sdf EBS device that is included in the AMI image
  community.aws.autoscaling_launch_config:
    name: special
    image_id: ami-XXX
    key_name: default
    security_groups: ['group', 'group2' ]
    instance_type: t1.micro
    volumes:
    - device_name: /dev/sdf
      no_device: true

- name: Use EBS snapshot ID for volume
  block:
  - name: Set Volume Facts
    ansible.builtin.set_fact:
      volumes:
      - device_name: /dev/sda1
        volume_size: 20
        ebs:
          snapshot: snap-XXXX
          volume_type: gp2
          delete_on_termination: true
          encrypted: false

  - name: Create launch configuration
    community.aws.autoscaling_launch_config:
      name: lc1
      image_id: ami-xxxx
      assign_public_ip: true
      instance_type: t2.medium
      key_name: my-key
      security_groups: "['sg-xxxx']"
      volumes: "{{ volumes }}"
    register: lc_info
"""

RETURN = r"""
arn:
  description: The Amazon Resource Name of the launch configuration.
  returned: when I(state=present)
  type: str
  sample: arn:aws:autoscaling:us-east-1:123456789012:launchConfiguration:888d9b58-d93a-40c4-90cf-759197a2621a:launchConfigurationName/launch_config_name
changed:
  description: Whether the state of the launch configuration has changed.
  returned: always
  type: bool
  sample: false
created_time:
  description: The creation date and time for the launch configuration.
  returned: when I(state=present)
  type: str
  sample: '2017-11-03 23:46:44.841000'
image_id:
  description: The ID of the Amazon Machine Image used by the launch configuration.
  returned: when I(state=present)
  type: str
  sample: ami-9be6f38c
instance_type:
  description: The instance type for the instances.
  returned: when I(state=present)
  type: str
  sample: t1.micro
name:
  description: The name of the launch configuration.
  returned: when I(state=present)
  type: str
  sample: launch_config_name
result:
  description: The specification details for the launch configuration.
  returned: when I(state=present)
  type: complex
  contains:
    PlacementTenancy:
      description: The tenancy of the instances, either default or dedicated.
      returned: when I(state=present)
      type: str
      sample: default
    associate_public_ip_address:
      description: (EC2-VPC) Indicates whether to assign a public IP address to each instance.
      returned: when I(state=present)
      type: bool
      sample: false
    block_device_mappings:
      description: A block device mapping, which specifies the block devices.
      returned: when I(state=present)
      type: complex
      contains:
        device_name:
          description: The device name exposed to the EC2 instance (for example, /dev/sdh or xvdh).
          returned: when I(state=present)
          type: str
          sample: /dev/sda1
        ebs:
          description: The information about the Amazon EBS volume.
          returned: when I(state=present)
          type: complex
          contains:
            snapshot_id:
              description: The ID of the snapshot.
              returned: when I(state=present)
              type: str
            volume_size:
              description: The volume size, in GiB.
              returned: when I(state=present)
              type: str
              sample: '100'
        virtual_name:
          description: The name of the virtual device (for example, ephemeral0).
          returned: when I(state=present)
          type: str
          sample: ephemeral0
    classic_link_vpc_id:
      description: The ID of a ClassicLink-enabled VPC to link your EC2-Classic instances to.
      returned: when I(state=present)
      type: str
    classic_link_vpc_security_groups:
      description: The IDs of one or more security groups for the VPC specified in ClassicLinkVPCId.
      returned: when I(state=present)
      type: list
      sample: []
    created_time:
      description: The creation date and time for the launch configuration.
      returned: when I(state=present)
      type: str
      sample: '2017-11-03 23:46:44.841000'
    delete_on_termination:
      description: Indicates whether the volume is deleted on instance termination.
      returned: when I(state=present)
      type: bool
      sample: true
    ebs_optimized:
      description: Indicates whether the instance is optimized for EBS I/O C(true) or not C(false).
      returned: when I(state=present)
      type: bool
      sample: false
    image_id:
      description: The ID of the Amazon Machine Image used by the launch configuration.
      returned: when I(state=present)
      type: str
      sample: ami-9be6f38c
    instance_monitoring:
      description: Indicates whether instances in this group are launched with detailed C(true) or basic C(false) monitoring.
      returned: when I(state=present)
      type: bool
      sample: true
    instance_profile_name:
      description: The name or Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instance.
      returned: when I(state=present)
      type: str
      sample: null
    instance_type:
      description: The instance type for the instances.
      returned: when I(state=present)
      type: str
      sample: t1.micro
    iops:
      description: The number of I/O operations per second (IOPS) to provision for the volume.
      returned: when I(state=present)
      type: int
    kernel_id:
      description: The ID of the kernel associated with the AMI.
      returned: when I(state=present)
      type: str
      sample: ''
    key_name:
      description: The name of the key pair.
      returned: when I(state=present)
      type: str
      sample: testkey
    launch_configuration_arn:
      description: The Amazon Resource Name (ARN) of the launch configuration.
      returned: when I(state=present)
      type: str
      sample: arn:aws:autoscaling:us-east-1:123456789012:launchConfiguration:888d9b58-d93a-40c4-90cf-759197a2621a:launchConfigurationName/launch_config_name
    member:
      description: ""
      returned: when I(state=present)
      type: str
      sample: "\n      "
    name:
      description: The name of the launch configuration.
      returned: when I(state=present)
      type: str
      sample: launch_config_name
    ramdisk_id:
      description: The ID of the RAM disk associated with the AMI.
      returned: when I(state=present)
      type: str
      sample: ''
    security_groups:
      description: The security groups to associate with the instances.
      returned: when I(state=present)
      type: list
      sample:
      - sg-5e27db2f
    spot_price:
      description: The price to bid when launching Spot Instances.
      returned: when I(state=present)
      type: float
    use_block_device_types:
      description: Indicates whether to suppress a device mapping.
      returned: when I(state=present)
      type: bool
      sample: false
    user_data:
      description: The user data available to the instances.
      returned: when I(state=present)
      type: str
      sample: ''
    volume_type:
      description: The volume type (one of standard, io1, gp2).
      returned: when I(state=present)
      type: str
      sample: io1
security_groups:
  description: The security groups to associate with the instances.
  returned: when I(state=present)
  type: list
  sample:
  - sg-5e27db2f
"""


import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_ec2_security_group_ids_from_names

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def create_block_device_meta(module, volume):
    if "snapshot" not in volume and "ephemeral" not in volume and "no_device" not in volume:
        if "volume_size" not in volume:
            module.fail_json(msg="Size must be specified when creating a new volume or modifying the root volume")
    if "snapshot" in volume:
        if volume.get("volume_type") == "io1" and "iops" not in volume:
            module.fail_json(msg="io1 volumes must have an iops value set")
    if "ephemeral" in volume:
        if "snapshot" in volume:
            module.fail_json(msg="Cannot set both ephemeral and snapshot")

    return_object = {}

    if "ephemeral" in volume:
        return_object["VirtualName"] = volume.get("ephemeral")

    if "device_name" in volume:
        return_object["DeviceName"] = volume.get("device_name")

    if "no_device" in volume:
        return_object["NoDevice"] = volume.get("no_device")

    if any(
        key in volume
        for key in [
            "snapshot",
            "volume_size",
            "volume_type",
            "delete_on_termination",
            "iops",
            "throughput",
            "encrypted",
        ]
    ):
        return_object["Ebs"] = {}

    if "snapshot" in volume:
        return_object["Ebs"]["SnapshotId"] = volume.get("snapshot")

    if "volume_size" in volume:
        return_object["Ebs"]["VolumeSize"] = int(volume.get("volume_size", 0))

    if "volume_type" in volume:
        return_object["Ebs"]["VolumeType"] = volume.get("volume_type")

    if "delete_on_termination" in volume:
        return_object["Ebs"]["DeleteOnTermination"] = volume.get("delete_on_termination", False)

    if "iops" in volume:
        return_object["Ebs"]["Iops"] = volume.get("iops")

    if "throughput" in volume:
        if volume.get("volume_type") != "gp3":
            module.fail_json(msg="The throughput parameter is supported only for GP3 volumes.")
        return_object["Ebs"]["Throughput"] = volume.get("throughput")

    if "encrypted" in volume:
        return_object["Ebs"]["Encrypted"] = volume.get("encrypted")

    return return_object


def create_launch_config(connection, module):
    name = module.params.get("name")
    vpc_id = module.params.get("vpc_id")
    try:
        ec2_connection = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")
    try:
        security_groups = get_ec2_security_group_ids_from_names(
            module.params.get("security_groups"), ec2_connection, vpc_id=vpc_id, boto3=True
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get Security Group IDs")
    except ValueError as e:
        module.fail_json(msg="Failed to get Security Group IDs", exception=traceback.format_exc())
    user_data = module.params.get("user_data")
    user_data_path = module.params.get("user_data_path")
    volumes = module.params["volumes"]
    instance_monitoring = module.params.get("instance_monitoring")
    assign_public_ip = module.params.get("assign_public_ip")
    instance_profile_name = module.params.get("instance_profile_name")
    ebs_optimized = module.params.get("ebs_optimized")
    classic_link_vpc_id = module.params.get("classic_link_vpc_id")
    classic_link_vpc_security_groups = module.params.get("classic_link_vpc_security_groups")

    block_device_mapping = []

    convert_list = [
        "image_id",
        "instance_type",
        "instance_type",
        "instance_id",
        "placement_tenancy",
        "key_name",
        "kernel_id",
        "ramdisk_id",
        "spot_price",
    ]

    launch_config = snake_dict_to_camel_dict(
        dict((k.capitalize(), str(v)) for k, v in module.params.items() if v is not None and k in convert_list)
    )

    if user_data_path:
        try:
            with open(user_data_path, "r") as user_data_file:
                user_data = user_data_file.read()
        except IOError as e:
            module.fail_json(msg="Failed to open file for reading", exception=traceback.format_exc())

    if volumes:
        for volume in volumes:
            if "device_name" not in volume:
                module.fail_json(msg="Device name must be set for volume")
            # Minimum volume size is 1GiB. We'll use volume size explicitly set to 0 to be a signal not to create this volume
            if "volume_size" not in volume or int(volume["volume_size"]) > 0:
                block_device_mapping.append(create_block_device_meta(module, volume))

    try:
        launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[name]).get(
            "LaunchConfigurations"
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe launch configuration by name")

    changed = False
    result = {}

    launch_config["LaunchConfigurationName"] = name

    if security_groups is not None:
        launch_config["SecurityGroups"] = security_groups

    if classic_link_vpc_id is not None:
        launch_config["ClassicLinkVPCId"] = classic_link_vpc_id

    if instance_monitoring is not None:
        launch_config["InstanceMonitoring"] = {"Enabled": instance_monitoring}

    if classic_link_vpc_security_groups is not None:
        launch_config["ClassicLinkVPCSecurityGroups"] = classic_link_vpc_security_groups

    if block_device_mapping:
        launch_config["BlockDeviceMappings"] = block_device_mapping

    if instance_profile_name is not None:
        launch_config["IamInstanceProfile"] = instance_profile_name

    if assign_public_ip is not None:
        launch_config["AssociatePublicIpAddress"] = assign_public_ip

    if user_data is not None:
        launch_config["UserData"] = user_data

    if ebs_optimized is not None:
        launch_config["EbsOptimized"] = ebs_optimized

    if len(launch_configs) == 0:
        try:
            connection.create_launch_configuration(**launch_config)
            launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[name]).get(
                "LaunchConfigurations"
            )
            changed = True
            if launch_configs:
                launch_config = launch_configs[0]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to create launch configuration")

    result = dict(
        (k, v)
        for k, v in launch_config.items()
        if k not in ["Connection", "CreatedTime", "InstanceMonitoring", "BlockDeviceMappings"]
    )

    result["CreatedTime"] = to_text(launch_config.get("CreatedTime"))

    try:
        result["InstanceMonitoring"] = module.boolean(launch_config.get("InstanceMonitoring").get("Enabled"))
    except AttributeError:
        result["InstanceMonitoring"] = False

    result["BlockDeviceMappings"] = []

    for block_device_mapping in launch_config.get("BlockDeviceMappings", []):
        result["BlockDeviceMappings"].append(
            dict(
                device_name=block_device_mapping.get("DeviceName"), virtual_name=block_device_mapping.get("VirtualName")
            )
        )
        if block_device_mapping.get("Ebs") is not None:
            result["BlockDeviceMappings"][-1]["ebs"] = dict(
                snapshot_id=block_device_mapping.get("Ebs").get("SnapshotId"),
                volume_size=block_device_mapping.get("Ebs").get("VolumeSize"),
            )

    if user_data_path:
        result["UserData"] = "hidden"  # Otherwise, we dump binary to the user's terminal

    return_object = {
        "Name": result.get("LaunchConfigurationName"),
        "CreatedTime": result.get("CreatedTime"),
        "ImageId": result.get("ImageId"),
        "Arn": result.get("LaunchConfigurationARN"),
        "SecurityGroups": result.get("SecurityGroups"),
        "InstanceType": result.get("InstanceType"),
        "Result": result,
    }

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(return_object))


def delete_launch_config(connection, module):
    try:
        name = module.params.get("name")
        launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[name]).get(
            "LaunchConfigurations"
        )
        if launch_configs:
            connection.delete_launch_configuration(
                LaunchConfigurationName=launch_configs[0].get("LaunchConfigurationName")
            )
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to delete launch configuration")


def main():
    argument_spec = dict(
        name=dict(required=True),
        image_id=dict(),
        instance_id=dict(),
        key_name=dict(),
        security_groups=dict(default=[], type="list", elements="str"),
        user_data=dict(),
        user_data_path=dict(type="path"),
        kernel_id=dict(),
        volumes=dict(type="list", elements="dict"),
        instance_type=dict(),
        state=dict(default="present", choices=["present", "absent"]),
        spot_price=dict(type="float"),
        ramdisk_id=dict(),
        instance_profile_name=dict(),
        ebs_optimized=dict(default=False, type="bool"),
        instance_monitoring=dict(default=False, type="bool"),
        assign_public_ip=dict(type="bool"),
        classic_link_vpc_security_groups=dict(type="list", elements="str"),
        classic_link_vpc_id=dict(),
        vpc_id=dict(),
        placement_tenancy=dict(choices=["default", "dedicated"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["user_data", "user_data_path"]],
    )

    try:
        connection = module.client("autoscaling")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="unable to establish connection")

    state = module.params.get("state")

    if state == "present":
        create_launch_config(connection, module)
    elif state == "absent":
        delete_launch_config(connection, module)


if __name__ == "__main__":
    main()
