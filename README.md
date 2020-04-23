

# Amazon AWS Collection
[![Shippable build status](https://api.shippable.com/projects/5e4451b6aa9a61000733064c/badge?branch=master)](https://api.shippable.com/projects/5e4451b6aa9a61000733064c/badge?branch=master)
<!--[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/amazon.aws)](https://codecov.io/gh/ansible-collections/amazon.aws)-->

The Ansible Amazon AWS collection includes a variety of Ansible content to help automate the management of AWS instances. This collection is maintained by the Ansible cloud team.

## Included content

Click the ``Content`` button to see the list of content included in this collection.

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


You can either call modules by their Fully Qualified Collection Namespace (FQCN), such as `amazon.aws.ec2_instance`, or you can call modules by their short name if you list the `ansible.aws` collection in the playbook's `collections` keyword:

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

You cal also join us on:

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

See [LICENCE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
