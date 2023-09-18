#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: aws_elasticbeanstalk_app
version_added: 1.0.0

short_description: Create, update, and delete an elastic beanstalk application


description:
    - Creates, updates, deletes beanstalk applications if app_name is provided.

options:
  app_name:
    description:
      - Name of the beanstalk application you wish to manage.
    aliases: [ 'name' ]
    type: str
  description:
    description:
      - The description of the application.
    type: str
  state:
    description:
      - Whether to ensure the application is present or absent.
    default: present
    choices: ['absent','present']
    type: str
  terminate_by_force:
    description:
      - When I(terminate_by_force=true), running environments will be terminated before deleting the application.
    default: false
    type: bool
author:
    - Harpreet Singh (@hsingh)
    - Stephen Granger (@viper233)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Create or update an application
- community.aws.aws_elasticbeanstalk_app:
    app_name: Sample_App
    description: "Hello World App"
    state: present

# Delete application
- community.aws.aws_elasticbeanstalk_app:
    app_name: Sample_App
    state: absent

'''

RETURN = '''
app:
    description: Beanstalk application.
    returned: always
    type: dict
    sample: {
        "ApplicationName": "app-name",
        "ConfigurationTemplates": [],
        "DateCreated": "2016-12-28T14:50:03.185000+00:00",
        "DateUpdated": "2016-12-28T14:50:03.185000+00:00",
        "Description": "description",
        "Versions": [
            "1.0.0",
            "1.0.1"
        ]
    }
output:
    description: Message indicating what change will occur.
    returned: in check mode
    type: str
    sample: App is up-to-date
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_message


def describe_app(ebs, app_name, module):
    apps = list_apps(ebs, app_name, module)

    return None if len(apps) != 1 else apps[0]


def list_apps(ebs, app_name, module):
    try:
        if app_name is not None:
            apps = ebs.describe_applications(ApplicationNames=[app_name])
        else:
            apps = ebs.describe_applications()
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Could not describe application")

    return apps.get("Applications", [])


def check_app(ebs, app, module):
    app_name = module.params['app_name']
    description = module.params['description']
    state = module.params['state']
    terminate_by_force = module.params['terminate_by_force']

    result = {}

    if state == 'present' and app is None:
        result = dict(changed=True, output="App would be created")
    elif state == 'present' and app.get("Description", None) != description:
        result = dict(changed=True, output="App would be updated", app=app)
    elif state == 'present' and app.get("Description", None) == description:
        result = dict(changed=False, output="App is up-to-date", app=app)
    elif state == 'absent' and app is None:
        result = dict(changed=False, output="App does not exist", app={})
    elif state == 'absent' and app is not None:
        result = dict(changed=True, output="App will be deleted", app=app)
    elif state == 'absent' and app is not None and terminate_by_force is True:
        result = dict(changed=True, output="Running environments terminated before the App will be deleted", app=app)

    module.exit_json(**result)


def filter_empty(**kwargs):
    retval = {}
    for k, v in kwargs.items():
        if v:
            retval[k] = v
    return retval


def main():
    argument_spec = dict(
        app_name=dict(aliases=['name'], type='str', required=False),
        description=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        terminate_by_force=dict(type='bool', default=False, required=False)
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    app_name = module.params['app_name']
    description = module.params['description']
    state = module.params['state']
    terminate_by_force = module.params['terminate_by_force']

    if app_name is None:
        module.fail_json(msg='Module parameter "app_name" is required')

    result = {}

    ebs = module.client('elasticbeanstalk')

    app = describe_app(ebs, app_name, module)

    if module.check_mode:
        check_app(ebs, app, module)
        module.fail_json(msg='ASSERTION FAILURE: check_app() should not return control.')

    if state == 'present':
        if app is None:
            try:
                create_app = ebs.create_application(**filter_empty(ApplicationName=app_name,
                                                    Description=description))
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Could not create application")

            app = describe_app(ebs, app_name, module)

            result = dict(changed=True, app=app)
        else:
            if app.get("Description", None) != description:
                try:
                    if not description:
                        ebs.update_application(ApplicationName=app_name)
                    else:
                        ebs.update_application(ApplicationName=app_name, Description=description)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Could not update application")

                app = describe_app(ebs, app_name, module)

                result = dict(changed=True, app=app)
            else:
                result = dict(changed=False, app=app)

    else:
        if app is None:
            result = dict(changed=False, output='Application not found', app={})
        else:
            try:
                if terminate_by_force:
                    # Running environments will be terminated before deleting the application
                    ebs.delete_application(ApplicationName=app_name, TerminateEnvByForce=terminate_by_force)
                else:
                    ebs.delete_application(ApplicationName=app_name)
                changed = True
            except is_boto3_error_message('It is currently pending deletion'):
                changed = False
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
                module.fail_json_aws(e, msg="Cannot terminate app")

            result = dict(changed=changed, app=app)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
