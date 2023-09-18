#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ecs_attribute
version_added: 1.0.0
short_description: manage ecs attributes
description:
    - Create, update or delete ECS container instance attributes.
author: Andrej Svenke (@anryko)
options:
    cluster:
        description:
            - The short name or full Amazon Resource Name (ARN) of the cluster
              that contains the resource to apply attributes.
        required: true
        type: str
    state:
        description:
            - The desired state of the attributes.
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
    attributes:
        description:
            - List of attributes.
        required: true
        type: list
        elements: dict
        suboptions:
            name:
                description:
                    - The name of the attribute. Up to 128 letters (uppercase and lowercase),
                      numbers, hyphens, underscores, and periods are allowed.
                required: true
                type: str
            value:
                description:
                    - The value of the attribute. Up to 128 letters (uppercase and lowercase),
                      numbers, hyphens, underscores, periods, at signs (@), forward slashes, colons,
                      and spaces are allowed.
                required: false
                type: str
    ec2_instance_id:
        description:
            - EC2 instance ID of ECS cluster container instance.
        required: true
        type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Set attributes
  community.aws.ecs_attribute:
    state: present
    cluster: test-cluster
    ec2_instance_id: "{{ ec2_id }}"
    attributes:
      - flavor: test
      - migrated
  delegate_to: localhost

- name: Delete attributes
  community.aws.ecs_attribute:
    state: absent
    cluster: test-cluster
    ec2_instance_id: "{{ ec2_id }}"
    attributes:
      - flavor: test
      - migrated
  delegate_to: localhost
'''

RETURN = r'''
attributes:
    description: attributes
    type: complex
    returned: always
    contains:
        cluster:
            description: cluster name
            type: str
        ec2_instance_id:
            description: ec2 instance id of ecs container instance
            type: str
        attributes:
            description: list of attributes
            type: list
            elements: dict
            contains:
                name:
                    description: name of the attribute
                    type: str
                value:
                    description: value of the attribute
                    returned: if present
                    type: str
'''

try:
    import botocore
    from botocore.exceptions import ClientError, EndpointConnectionError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


class EcsAttributes(object):
    """Handles ECS Cluster Attribute"""

    def __init__(self, module, attributes):
        self.module = module
        self.attributes = attributes if self._validate_attrs(attributes) else self._parse_attrs(attributes)

    def __bool__(self):
        return bool(self.attributes)

    __nonzero__ = __bool__

    def __iter__(self):
        return iter(self.attributes)

    @staticmethod
    def _validate_attrs(attrs):
        return all(tuple(attr.keys()) in (('name', 'value'), ('value', 'name')) for attr in attrs)

    def _parse_attrs(self, attrs):
        attrs_parsed = []
        for attr in attrs:
            if isinstance(attr, dict):
                if len(attr) != 1:
                    self.module.fail_json(msg="Incorrect attribute format - %s" % str(attr))
                name, value = list(attr.items())[0]
                attrs_parsed.append({'name': name, 'value': value})
            elif isinstance(attr, str):
                attrs_parsed.append({'name': attr, 'value': None})
            else:
                self.module.fail_json(msg="Incorrect attributes format - %s" % str(attrs))

        return attrs_parsed

    def _setup_attr_obj(self, ecs_arn, name, value=None, skip_value=False):
        attr_obj = {'targetType': 'container-instance',
                    'targetId': ecs_arn,
                    'name': name}
        if not skip_value and value is not None:
            attr_obj['value'] = value

        return attr_obj

    def get_for_ecs_arn(self, ecs_arn, skip_value=False):
        """
        Returns list of attribute dicts ready to be passed to boto3
        attributes put/delete methods.
        """
        return [self._setup_attr_obj(ecs_arn, skip_value=skip_value, **attr) for attr in self.attributes]

    def diff(self, attrs):
        """
        Returns EcsAttributes Object containing attributes which are present
        in self but are absent in passed attrs (EcsAttributes Object).
        """
        attrs_diff = [attr for attr in self.attributes if attr not in attrs]
        return EcsAttributes(self.module, attrs_diff)


class Ec2EcsInstance(object):
    """Handle ECS Cluster Remote Operations"""

    def __init__(self, module, cluster, ec2_id):
        self.module = module
        self.cluster = cluster
        self.ec2_id = ec2_id

        try:
            self.ecs = module.client('ecs')
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to connect to AWS')

        self.ecs_arn = self._get_ecs_arn()

    def _get_ecs_arn(self):
        try:
            ecs_instances_arns = self.ecs.list_container_instances(cluster=self.cluster)['containerInstanceArns']
            ec2_instances = self.ecs.describe_container_instances(cluster=self.cluster,
                                                                  containerInstances=ecs_instances_arns)['containerInstances']
        except (ClientError, EndpointConnectionError) as e:
            self.module.fail_json(msg="Can't connect to the cluster - %s" % str(e))

        try:
            ecs_arn = next(inst for inst in ec2_instances
                           if inst['ec2InstanceId'] == self.ec2_id)['containerInstanceArn']
        except StopIteration:
            self.module.fail_json(msg="EC2 instance Id not found in ECS cluster - %s" % str(self.cluster))

        return ecs_arn

    def attrs_put(self, attrs):
        """Puts attributes on ECS container instance"""
        try:
            self.ecs.put_attributes(cluster=self.cluster,
                                    attributes=attrs.get_for_ecs_arn(self.ecs_arn))
        except ClientError as e:
            self.module.fail_json(msg=str(e))

    def attrs_delete(self, attrs):
        """Deletes attributes from ECS container instance."""
        try:
            self.ecs.delete_attributes(cluster=self.cluster,
                                       attributes=attrs.get_for_ecs_arn(self.ecs_arn, skip_value=True))
        except ClientError as e:
            self.module.fail_json(msg=str(e))

    def attrs_get_by_name(self, attrs):
        """
        Returns EcsAttributes object containing attributes from ECS container instance with names
        matching to attrs.attributes (EcsAttributes Object).
        """
        attr_objs = [{'targetType': 'container-instance', 'attributeName': attr['name']}
                     for attr in attrs]

        try:
            matched_ecs_targets = [attr_found for attr_obj in attr_objs
                                   for attr_found in self.ecs.list_attributes(cluster=self.cluster, **attr_obj)['attributes']]
        except ClientError as e:
            self.module.fail_json(msg="Can't connect to the cluster - %s" % str(e))

        matched_objs = [target for target in matched_ecs_targets
                        if target['targetId'] == self.ecs_arn]

        results = [{'name': match['name'], 'value': match.get('value', None)}
                   for match in matched_objs]

        return EcsAttributes(self.module, results)


def main():
    argument_spec = dict(
        state=dict(required=False, default='present', choices=['present', 'absent']),
        cluster=dict(required=True, type='str'),
        ec2_instance_id=dict(required=True, type='str'),
        attributes=dict(required=True, type='list', elements='dict'),
    )

    required_together = [['cluster', 'ec2_instance_id', 'attributes']]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=required_together,
    )

    cluster = module.params['cluster']
    ec2_instance_id = module.params['ec2_instance_id']
    attributes = module.params['attributes']

    conti = Ec2EcsInstance(module, cluster, ec2_instance_id)
    attrs = EcsAttributes(module, attributes)

    results = {'changed': False,
               'attributes': [
                   {'cluster': cluster,
                    'ec2_instance_id': ec2_instance_id,
                    'attributes': attributes}
               ]}

    attrs_present = conti.attrs_get_by_name(attrs)

    if module.params['state'] == 'present':
        attrs_diff = attrs.diff(attrs_present)
        if not attrs_diff:
            module.exit_json(**results)

        conti.attrs_put(attrs_diff)
        results['changed'] = True

    elif module.params['state'] == 'absent':
        if not attrs_present:
            module.exit_json(**results)

        conti.attrs_delete(attrs_present)
        results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
