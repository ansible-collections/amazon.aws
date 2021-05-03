# Amazon AWS Collection
[![Shippable build status](https://api.shippable.com/projects/5e4451b6aa9a61000733064c/badge?branch=main)](https://api.shippable.com/projects/5e4451b6aa9a61000733064c/badge?branch=main)
[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/amazon.aws)](https://codecov.io/gh/ansible-collections/amazon.aws)

The Ansible Amazon AWS collection includes a variety of Ansible content to help automate the management of AWS instances. This collection is maintained by the Ansible cloud team.

AWS related modules and plugins supported by the Ansible community are in the [community.aws](https://github.com/ansible-collections/community.aws/) collection.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.10**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

## Python version compatibility

This collection depends on the AWS SDK for Python (Boto3 and Botocore). As AWS has [ceased supporting Python 2.6](https://aws.amazon.com/blogs/developer/deprecation-of-python-2-6-and-python-3-3-in-botocore-boto3-and-the-aws-cli/), this collection requires Python 2.7 or greater.

## Included content

<!--start collection content-->
### Inventory plugins
Name | Description
--- | ---
[amazon.aws.aws_ec2](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_ec2_inventory.rst)|EC2 inventory source
[amazon.aws.aws_rds](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_rds_inventory.rst)|rds instance source

### Lookup plugins
Name | Description
--- | ---
[amazon.aws.aws_account_attribute](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_account_attribute_lookup.rst)|Look up AWS account attributes.
[amazon.aws.aws_secret](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_secret_lookup.rst)|Look up secrets stored in AWS Secrets Manager.
[amazon.aws.aws_service_ip_ranges](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_service_ip_ranges_lookup.rst)|Look up the IP ranges for services provided in AWS such as EC2 and S3.
[amazon.aws.aws_ssm](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_ssm_lookup.rst)|Get the value for a SSM parameter or all parameters under a path.

### Modules
Name | Description
--- | ---
[amazon.aws.aws_az_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_az_info_module.rst)|Gather information about availability zones in AWS.
[amazon.aws.aws_caller_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_caller_info_module.rst)|Get information about the user and account being used to make AWS calls.
[amazon.aws.aws_s3](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.aws_s3_module.rst)|manage objects in S3.
[amazon.aws.cloudformation](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.cloudformation_module.rst)|Create or delete an AWS CloudFormation stack
[amazon.aws.cloudformation_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.cloudformation_info_module.rst)|Obtain information about an AWS CloudFormation stack
[amazon.aws.ec2](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_module.rst)|create, terminate, start or stop an instance in ec2
[amazon.aws.ec2_ami](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_ami_module.rst)|Create or destroy an image (AMI) in ec2
[amazon.aws.ec2_ami_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_ami_info_module.rst)|Gather information about ec2 AMIs
[amazon.aws.ec2_elb_lb](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_elb_lb_module.rst)|Creates, updates or destroys an Amazon ELB.
[amazon.aws.ec2_eni](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_eni_module.rst)|Create and optionally attach an Elastic Network Interface (ENI) to an instance
[amazon.aws.ec2_eni_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_eni_info_module.rst)|Gather information about ec2 ENI interfaces in AWS
[amazon.aws.ec2_group](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_group_module.rst)|maintain an ec2 VPC security group.
[amazon.aws.ec2_group_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_group_info_module.rst)|Gather information about ec2 security groups in AWS.
[amazon.aws.ec2_key](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_key_module.rst)|create or delete an ec2 key pair
[amazon.aws.ec2_metadata_facts](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_metadata_facts_module.rst)|gathers facts (instance metadata) about remote hosts within EC2
[amazon.aws.ec2_snapshot](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_snapshot_module.rst)|Creates a snapshot from an existing volume
[amazon.aws.ec2_snapshot_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_snapshot_info_module.rst)|Gather information about ec2 volume snapshots in AWS
[amazon.aws.ec2_tag](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_tag_module.rst)|create and remove tags on ec2 resources
[amazon.aws.ec2_tag_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_tag_info_module.rst)|list tags on ec2 resources
[amazon.aws.ec2_vol](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vol_module.rst)|Create and attach a volume, return volume id and device map
[amazon.aws.ec2_vol_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vol_info_module.rst)|Gather information about ec2 volumes in AWS
[amazon.aws.ec2_vpc_dhcp_option](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vpc_dhcp_option_module.rst)|Manages DHCP Options, and can ensure the DHCP options for the given VPC match what's requested
[amazon.aws.ec2_vpc_dhcp_option_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vpc_dhcp_option_info_module.rst)|Gather information about dhcp options sets in AWS
[amazon.aws.ec2_vpc_net](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vpc_net_module.rst)|Configure AWS virtual private clouds
[amazon.aws.ec2_vpc_net_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vpc_net_info_module.rst)|Gather information about ec2 VPCs in AWS
[amazon.aws.ec2_vpc_subnet](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vpc_subnet_module.rst)|Manage subnets in AWS virtual private clouds
[amazon.aws.ec2_vpc_subnet_info](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.ec2_vpc_subnet_info_module.rst)|Gather information about ec2 VPC subnets in AWS
[amazon.aws.s3_bucket](https://github.com/ansible-collections/amazon.aws/blob/main/docs/amazon.aws.s3_bucket_module.rst)|Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID

<!--end collection content-->

## Installing this collection

You can install the AWS collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install amazon.aws

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: amazon.aws
```

The python module dependencies are not installed by `ansible-galaxy`.  They can
be manually installed using pip:

    pip install requirements.txt

or:

    pip install boto boto3 botocore

## Using this collection


You can either call modules by their Fully Qualified Collection Namespace (FQCN), such as `amazon.aws.ec2_instance`, or you can call modules by their short name if you list the `amazon.aws` collection in the playbook's `collections` keyword:

```yaml
---
  - name: Setup an instance for testing
    amazon.aws.ec2_instance:
      name: '{{ resource_prefix }}'
      instance_type: t2.nano
      image_id: "{{ (amis.images | sort(attribute='creation_date') | last).image_id }}"
      wait: yes
      volumes:
        - device_name: /dev/xvda
          ebs:
            volume_size: 8
            delete_on_termination: true
    register: instance
```

**NOTE**: For Ansible 2.9, you may not see deprecation warnings when you run your playbooks with this collection. Use this documentation to track when a module is deprecated.


### See Also:

* [Amazon Web Services Guide](https://docs.ansible.com/ansible/latest/scenario_guides/guide_aws.html)
* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Amazon AWS collection repository](https://github.com/ansible-collections/amazon.aws). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for more details.

You can also join us on:

- Freenode IRC - ``#ansible-aws`` Freenode channel

### More information about contributing

- [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) - Details on contributing to Ansible
- [Contributing to Collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) - How to check out collection git repositories correctly
- [Guidelines for Ansible Amazon AWS module development](https://docs.ansible.com/ansible/latest/dev_guide/platforms/aws_guidelines.html)
- [Getting Started With AWS Ansible Module Development and Community Contribution](https://www.ansible.com/blog/getting-started-with-aws-ansible-module-development)

## Release notes
<!--Add a link to a changelog.rst file or an external docsite to cover this information. -->

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
