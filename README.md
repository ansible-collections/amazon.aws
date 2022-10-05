# Amazon AWS Collection
The Ansible Amazon AWS collection includes a variety of Ansible content to help automate the management of AWS instances. This collection is maintained by the Ansible cloud team.

AWS related modules and plugins supported by the Ansible community are in the [community.aws](https://github.com/ansible-collections/community.aws/) collection.

## Ansible version compatibility

Tested with the Ansible Core 2.12, and 2.13 releases, and the current development version of Ansible. Ansible Core versions before 2.11.0 are not supported. In particular, Ansible Core 2.10 and Ansible 2.9 are not supported.

Use amazon.aws 4.x.y if you are using Ansible 2.9 or Ansible Core 2.10.

## Python version compatibility

This collection depends on the AWS SDK for Python (Boto3 and Botocore).  Due to the
[AWS SDK Python Support Policy](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/)
this collection requires Python 3.6 or greater.

Amazon have also announced the end of support for
[Python less than 3.7](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/).
As such support for Python less than 3.7 by this collection has been deprecated and will be removed in a release
after 2023-05-31.

## AWS SDK version compatibility

Starting with the 2.0.0 releases of amazon.aws and community.aws, it is generally the collection's policy to support the versions of `botocore` and `boto3` that were released 12 months prior to the most recent major collection release, following semantic versioning (for example, 2.0.0, 3.0.0).

Version 5.0.0 of this collection supports `boto3 >= 1.18.0` and `botocore >= 1.21.0`

All support for the original AWS SDK `boto` was removed in release 4.0.0.

## Included content
<!--start collection content-->
See the complete list of collection content in the [Plugin Index](https://ansible-collections.github.io/amazon.aws/branch/stable-5/collections/amazon/aws/index.html#plugin-index).

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

A specific version of the collection can be installed by using the `version` keyword in the `requirements.yml` file:

```yaml
---
collections:
  - name: amazon.aws
    version: 3.1.1
```

The python module dependencies are not installed by `ansible-galaxy`.  They can
be manually installed using pip:

    pip install -r requirements.txt

or:

    pip install boto3 botocore

## Using this collection

You can either call modules by their Fully Qualified Collection Name (FQCN), such as `amazon.aws.ec2_instance`, or you can call modules by their short name if you list the `amazon.aws` collection in the playbook's `collections` keyword:

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
See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for more details.

You can also join us on:

- Libera.Chat IRC - the ``#ansible-aws`` [irc.libera.chat](https://libera.chat/) channel

### More information about contributing

- [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) - Details on contributing to Ansible
- [Contributing to Collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) - How to check out collection git repositories correctly
- [Guidelines for Ansible Amazon AWS module development](https://docs.ansible.com/ansible/latest/dev_guide/platforms/aws_guidelines.html)
- [Getting Started With AWS Ansible Module Development and Community Contribution](https://www.ansible.com/blog/getting-started-with-aws-ansible-module-development)

## Release notes

See the [rendered changelog](https://ansible-collections.github.io/amazon.aws/branch/stable-5/collections/amazon/aws/docsite/CHANGELOG.html) or the [raw generated changelog](https://github.com/ansible-collections/amazon.aws/tree/stable-5/CHANGELOG.rst).

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collection Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
