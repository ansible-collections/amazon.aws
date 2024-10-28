# Amazon AWS Collection
The Ansible Amazon AWS collection includes a variety of Ansible content to help automate the management of AWS services. This collection is maintained by the Ansible cloud team.

## Description

The primary purpose of this collection is to simplify and streamline the management of AWS resources through automation. By leveraging this collection, organizations can reduce manual intervention, minimize errors, and ensure consistent and repeatable deployments. This leads to increased efficiency, faster deployments, and a more agile IT infrastructure.

AWS related modules and plugins supported by the Ansible community are in the [community.aws](https://github.com/ansible-collections/community.aws/) collection.

Being Red Hat Ansible Certified Content, this collection is eligible for support through the [Ansible Automation Platform](https://www.redhat.com/en/technologies/management/ansible).

## Communication

* Join the Ansible forum:
  * [Get Help](https://forum.ansible.com/c/help/6): get help or help others.
  * [Posts tagged with 'aws'](https://forum.ansible.com/tag/aws): subscribe to participate in collection-related conversations.
  * [AWS Working Group](https://forum.ansible.com/g/AWS): by joining the team you will automatically get subscribed to the posts tagged with [aws](https://forum.ansible.com/tags).
  * [Social Spaces](https://forum.ansible.com/c/chat/4): gather and interact with fellow enthusiasts.
  * [News & Announcements](https://forum.ansible.com/c/news/5): track project-wide announcements including social events.

* The Ansible [Bullhorn newsletter](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn): used to announce releases and important changes.

For more information about communication, see the [Ansible communication guide](https://docs.ansible.com/ansible/devel/community/communication.html).

## Requirements

### Ansible version compatibility

Tested with the Ansible Core >= 2.15.0 versions, and the current development version of Ansible. Ansible Core versions prior to 2.15.0 are not supported.

### Python version compatibility

This collection depends on the AWS SDK for Python (Boto3 and Botocore).  Due to the
[AWS SDK Python Support Policy](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/)
this collection requires Python 3.7 or greater.

Amazon has also announced the planned end of support for
[Python less than 3.8](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/).
As such support for Python less than 3.8 will be removed in a release after 2024-12-01.

<!---
### End of Support by Python Versions:

| Python Version | AWS SDK | Collection |
| -------------- | -------- | ---------- |
| 2.7 | July 2021 | Release 2.0.0 (September 2021) |
| 3.4 | February 2021 | Release 1.0.0 (June 2020) |
| 3.5 | February 2021 | Release 2.0.0 (September 2021) |
| 3.6 | May 2022 | Release 7.0.0 (November 2023) |
| 3.7 | December 2023 | *After December 2024* |
| 3.8 | April 2025 | *After April 2026* |
| 3.9 | April 2026 | *After April 2027* |
| 3.10 | April 2027 | *After April 2028* |
| 3.11 | April 2028 | *After April 2029* |
--->

### AWS SDK version compatibility

Starting with the 2.0.0 releases of amazon.aws and community.aws, it is generally the collection's policy to support the versions of `botocore` and `boto3` that were released 12 months prior to the most recent major collection release, following semantic versioning (for example, 2.0.0, 3.0.0).

Version 9.0.0 of this collection supports `boto3 >= 1.28.0` and `botocore >= 1.31.0`

All support for the original AWS SDK `boto` was removed in release 4.0.0.

## Included content
<!--start collection content-->
See the complete list of collection content in the [Plugin Index](https://ansible-collections.github.io/amazon.aws/branch/stable-9/collections/amazon/aws/index.html#plugin-index).

<!--end collection content-->

## Installation

The amazon.aws collection can be installed with Ansible Galaxy command-line tool:

```
    ansible-galaxy collection install amazon.aws
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: amazon.aws
```

Note that if you install any collections from Ansible Galaxy, they will not be upgraded automatically when you upgrade the Ansible package.
To upgrade the collection to the latest available version, run the following command:

```
ansible-galaxy collection install amazon.aws --upgrade
```
A specific version of the collection can be installed by using the `version` keyword in the `requirements.yml` file:

```yaml
---
collections:
  - name: amazon.aws
    version: 3.1.1
```

or using the ansible-galaxy command as follows

```
ansible-galaxy collection install amazon.aws:==1.0.0
```

The python module dependencies are not installed by `ansible-galaxy`.  They can
be manually installed using pip:

    pip install -r requirements.txt

or:

    pip install boto3 botocore

Refer the following for more details.
* [Amazon Web Services Guide](https://docs.ansible.com/ansible/latest/collections/amazon/aws/docsite/guide_aws.html)
* [using Ansible collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Use Cases

You can either call modules by their Fully Qualified Collection Name (FQCN), such as `amazon.aws.ec2_instance`, or you can call modules by their short name if you list the `amazon.aws` collection in the playbook's `collections` keyword:

```yaml
---
  - name: Setup an instance for testing
    amazon.aws.ec2_instance:
      name: '{{ ec2_instance_name }}'
      instance_type: t2.nano
      image_id: "{{ (amis.images | sort(attribute='creation_date') | last).image_id }}"
      wait: yes
      volumes:
        - device_name: /dev/xvda
          ebs:
            volume_size: 8
            delete_on_termination: true
    register: instance

  - name: Gather {{ ec2_instance_name }} info
    amazon.aws.ec2_instance_info:
      filters:
        tag:Name: "{{ ec2_instance_name }}"
        include_attributes:
          - instanceType
          - kernel
          - ramdisk
          - userData
          - disableApiTermination
          - instanceInitiatedShutdownBehavior
          - rootDeviceName
          - blockDeviceMapping
          - productCodes
          - sourceDestCheck
          - groupSet
          - ebsOptimized
          - sriovNetSupport
          - enclaveOptions
      register: instance_info

  - name: Delete instance created for tests
    amazon.aws.ec2_instance:
      state: absent
      instance_ids: "{{ instance.instance_ids }}"
      wait: false
```

## Testing

This collection is tested using GitHub Actions. To know more about testing, refer to [CI.md](https://github.com/ansible-collections/amazon.aws/blob/stable-9/CI.md).

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Amazon AWS collection repository](https://github.com/ansible-collections/amazon.aws).
See [CONTRIBUTING.md](https://github.com/ansible-collections/amazon.aws/blob/stable-9/CONTRIBUTING.md) for more details.

### More information about contributing

- [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) - Details on contributing to Ansible
- [Contributing to Collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) - How to check out collection git repositories correctly
- [Guidelines for Ansible Amazon AWS module development](https://docs.ansible.com/ansible/latest/collections/amazon/aws/docsite/dev_guidelines.html)
- [Getting Started With AWS Ansible Module Development and Community Contribution](https://www.ansible.com/blog/getting-started-with-aws-ansible-module-development)

## Support

You can also join us on:

- Libera.Chat IRC - the ``#ansible-aws`` [irc.libera.chat](https://libera.chat/) channel

## Release notes

See the [rendered changelog](https://ansible-collections.github.io/amazon.aws/branch/stable-9/collections/amazon/aws/docsite/CHANGELOG.html) or the [raw generated changelog](https://github.com/ansible-collections/amazon.aws/tree/stable-9/CHANGELOG.rst).

## Related Information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collection Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## License Information

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
