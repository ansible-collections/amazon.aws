

# Amazon AWS Collection
[![Shippable build status](https://api.shippable.com/projects/5e4451b6aa9a61000733064c/badge?branch=master)](https://api.shippable.com/projects/5e4451b6aa9a61000733064c/badge?branch=master)
<!--[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/amazon.aws)](https://codecov.io/gh/ansible-collections/amazon.aws)-->

The Ansible Amazon AWS collection includes a variety of Ansible content to help automate the management of AWS instances. This collection is maintained by the Ansible cloud team.

## Included content

<!--start collection content-->
## Modules
Name | Description
--- | ---
[amazon.aws.aws_az_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.aws_az_info.rst)|Gather information about availability zones in AWS.
[amazon.aws.aws_caller_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.aws_caller_info.rst)|Get information about the user and account being used to make AWS calls.
[amazon.aws.aws_s3](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.aws_s3.rst)|manage objects in S3.
[amazon.aws.cloudformation](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.cloudformation.rst)|Create or delete an AWS CloudFormation stack
[amazon.aws.cloudformation_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.cloudformation_info.rst)|Obtain information about an AWS CloudFormation stack
[amazon.aws.ec2](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2.rst)|create, terminate, start or stop an instance in ec2
[amazon.aws.ec2_ami](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_ami.rst)|Create or destroy an image (AMI) in ec2
[amazon.aws.ec2_ami_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_ami_info.rst)|Gather information about ec2 AMIs
[amazon.aws.ec2_elb_lb](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_elb_lb.rst)|Creates, updates or destroys an Amazon ELB.
[amazon.aws.ec2_eni](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_eni.rst)|Create and optionally attach an Elastic Network Interface (ENI) to an instance
[amazon.aws.ec2_eni_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_eni_info.rst)|Gather information about ec2 ENI interfaces in AWS
[amazon.aws.ec2_group](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_group.rst)|maintain an ec2 VPC security group.
[amazon.aws.ec2_group_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_group_info.rst)|Gather information about ec2 security groups in AWS.
[amazon.aws.ec2_key](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_key.rst)|create or delete an ec2 key pair
[amazon.aws.ec2_metadata_facts](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_metadata_facts.rst)|Gathers facts (instance metadata) about remote hosts within ec2
[amazon.aws.ec2_snapshot](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_snapshot.rst)|Creates a snapshot from an existing volume
[amazon.aws.ec2_snapshot_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_snapshot_info.rst)|Gather information about ec2 volume snapshots in AWS
[amazon.aws.ec2_tag](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_tag.rst)|create and remove tags on ec2 resources
[amazon.aws.ec2_tag_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_tag_info.rst)|list tags on ec2 resources
[amazon.aws.ec2_vol](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vol.rst)|Create and attach a volume, return volume id and device map
[amazon.aws.ec2_vol_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vol_info.rst)|Gather information about ec2 volumes in AWS
[amazon.aws.ec2_vpc_dhcp_option](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vpc_dhcp_option.rst)|Manages DHCP Options, and can ensure the DHCP options for the given VPC match what's requested
[amazon.aws.ec2_vpc_dhcp_option_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vpc_dhcp_option_info.rst)|Gather information about dhcp options sets in AWS
[amazon.aws.ec2_vpc_net](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vpc_net.rst)|Configure AWS virtual private clouds
[amazon.aws.ec2_vpc_net_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vpc_net_info.rst)|Gather information about ec2 VPCs in AWS
[amazon.aws.ec2_vpc_subnet](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vpc_subnet.rst)|Manage subnets in AWS virtual private clouds
[amazon.aws.ec2_vpc_subnet_info](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.ec2_vpc_subnet_info.rst)|Gather information about ec2 VPC subnets in AWS
[amazon.aws.s3_bucket](https://github.com/ansible-collections/amazon.aws.git/blob/master/docs/amazon.aws.s3_bucket.rst)|Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID
<!--end collection content-->

## Installing this collection

You can install the AWS collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install amazon.aws

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: amazon.aws
    version: 0.1.1
```
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


### See Also:

* [Amazon Web Services Guide](https://docs.ansible.com/ansible/latest/scenario_guides/guide_aws.html)
* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Amazon AWS collection repository](https://github.com/ansible-collections/amazon.aws).

You can also join us on:

- Freenode IRC - ``#ansible-aws`` Freenode channel

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.


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

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.