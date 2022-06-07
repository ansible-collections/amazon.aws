#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
---
module: aws_codebuild
version_added: 1.0.0
short_description: Create or delete an AWS CodeBuild project
notes:
    - For details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html).
description:
    - Create or delete a CodeBuild projects on AWS, used for building code artifacts from source code.
author:
    - Stefan Horning (@stefanhorning) <horning@mediapeers.com>
options:
    name:
        description:
            - Name of the CodeBuild project.
        required: true
        type: str
    description:
        description:
            - Descriptive text of the CodeBuild project.
        type: str
    source:
        description:
            - Configure service and location for the build input source.
            - I(source) is required when creating a new project.
        suboptions:
            type:
                description:
                    - "The type of the source. Allows one of these: C(CODECOMMIT), C(CODEPIPELINE), C(GITHUB), C(S3), C(BITBUCKET), C(GITHUB_ENTERPRISE)."
                required: true
                type: str
            location:
                description:
                    - Information about the location of the source code to be built. For type CODEPIPELINE location should not be specified.
                type: str
            git_clone_depth:
                description:
                    - When using git you can specify the clone depth as an integer here.
                type: int
            buildspec:
                description:
                    - The build spec declaration to use for the builds in this build project. Leave empty if part of the code project.
                type: str
            insecure_ssl:
                description:
                    - Enable this flag to ignore SSL warnings while connecting to the project source code.
                type: bool
        type: dict
    artifacts:
        description:
            - Information about the build output artifacts for the build project.
            - I(artifacts) is required when creating a new project.
        suboptions:
            type:
                description:
                    - "The type of build output for artifacts. Can be one of the following: C(CODEPIPELINE), C(NO_ARTIFACTS), C(S3)."
                required: true
            location:
                description:
                    - Information about the build output artifact location. When choosing type S3, set the bucket name here.
            path:
                description:
                    - Along with namespace_type and name, the pattern that AWS CodeBuild will use to name and store the output artifacts.
                    - Used for path in S3 bucket when type is C(S3).
            namespace_type:
                description:
                    - Along with path and name, the pattern that AWS CodeBuild will use to determine the name and location to store the output artifacts.
                    - Accepts C(BUILD_ID) and C(NONE).
                    - "See docs here: U(http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html#CodeBuild.Client.create_project)."
            name:
                description:
                    - Along with path and namespace_type, the pattern that AWS CodeBuild will use to name and store the output artifact.
            packaging:
                description:
                    - The type of build output artifact to create on S3, can be NONE for creating a folder or ZIP for a ZIP file.
        type: dict
    cache:
        description:
            - Caching params to speed up following builds.
        suboptions:
            type:
                description:
                    - Cache type. Can be C(NO_CACHE) or C(S3).
                required: true
            location:
                description:
                    - Caching location on S3.
                required: true
        type: dict
    environment:
        description:
            - Information about the build environment for the build project.
        suboptions:
            type:
                description:
                    - The type of build environment to use for the project. Usually C(LINUX_CONTAINER).
                required: true
            image:
                description:
                    - The ID of the Docker image to use for this build project.
                required: true
            compute_type:
                description:
                    - Information about the compute resources the build project will use.
                    - "Available values include: C(BUILD_GENERAL1_SMALL), C(BUILD_GENERAL1_MEDIUM), C(BUILD_GENERAL1_LARGE)."
                required: true
            environment_variables:
                description:
                    - A set of environment variables to make available to builds for the build project. List of dictionaries with name and value fields.
                    - "Example: { name: 'MY_ENV_VARIABLE', value: 'test' }"
            privileged_mode:
                description:
                    - Enables running the Docker daemon inside a Docker container. Set to true only if the build project is be used to build Docker images.
        type: dict
    service_role:
        description:
            - The ARN of the AWS IAM role that enables AWS CodeBuild to interact with dependent AWS services on behalf of the AWS account.
        type: str
    timeout_in_minutes:
        description:
            - How long CodeBuild should wait until timing out any build that has not been marked as completed.
        default: 60
        type: int
    encryption_key:
        description:
            - The AWS Key Management Service (AWS KMS) customer master key (CMK) to be used for encrypting the build output artifacts.
        type: str
    tags:
        description:
            - A set of tags for the build project.
            - Mutually exclusive with the I(resource_tags) parameter.
            - In release 6.0.0 this parameter will accept a simple dictionary
              instead of the list of dictionaries format.  To use the simple
              dictionary format prior to release 6.0.0 the I(resource_tags) can
              be used instead of I(tags).
        type: list
        elements: dict
        suboptions:
            key:
                description: The name of the Tag.
                type: str
            value:
                description: The value of the Tag.
                type: str
    vpc_config:
        description:
            - The VPC config enables AWS CodeBuild to access resources in an Amazon VPC.
        type: dict
    state:
        description:
            - Create or remove code build project.
        default: 'present'
        choices: ['present', 'absent']
        type: str
    resource_tags:
        description:
            - A dictionary representing the tags to be applied to the build project.
            - If the I(resource_tags) parameter is not set then tags will not be modified.
            - Mutually exclusive with the I(tags) parameter.
        type: dict
        required: false
    purge_tags:
        description:
            - If I(purge_tags=true) and I(tags) is set, existing tags will be purged
              from the resource to match exactly what is defined by I(tags) parameter.
            - If the I(resource_tags) parameter is not set then tags will not be modified, even
              if I(purge_tags=True).
            - Tag keys beginning with C(aws:) are reserved by Amazon and can not be
              modified.  As such they will be ignored for the purposes of the
              I(purge_tags) parameter.  See the Amazon documentation for more information
              U(https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions).
        type: bool
        default: true
        required: false

extends_documentation_fragment:
    - amazon.aws.aws
    - amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- community.aws.aws_codebuild:
    name: my_project
    description: My nice little project
    service_role: "arn:aws:iam::123123:role/service-role/code-build-service-role"
    source:
        # Possible values: BITBUCKET, CODECOMMIT, CODEPIPELINE, GITHUB, S3
        type: CODEPIPELINE
        buildspec: ''
    artifacts:
        namespaceType: NONE
        packaging: NONE
        type: CODEPIPELINE
        name: my_project
    environment:
        computeType: BUILD_GENERAL1_SMALL
        privilegedMode: "true"
        image: "aws/codebuild/docker:17.09.0"
        type: LINUX_CONTAINER
        environmentVariables:
            - { name: 'PROFILE', value: 'staging' }
    encryption_key: "arn:aws:kms:us-east-1:123123:alias/aws/s3"
    region: us-east-1
    state: present
'''

RETURN = r'''
project:
  description: Returns the dictionary describing the code project configuration.
  returned: success
  type: complex
  contains:
    name:
      description: Name of the CodeBuild project
      returned: always
      type: str
      sample: my_project
    arn:
      description: ARN of the CodeBuild project
      returned: always
      type: str
      sample: arn:aws:codebuild:us-east-1:123123123:project/vod-api-app-builder
    description:
      description: A description of the build project
      returned: always
      type: str
      sample: My nice little project
    source:
      description: Information about the build input source code.
      returned: always
      type: complex
      contains:
        type:
          description: The type of the repository
          returned: always
          type: str
          sample: CODEPIPELINE
        location:
          description: Location identifier, depending on the source type.
          returned: when configured
          type: str
        git_clone_depth:
          description: The git clone depth
          returned: when configured
          type: int
        build_spec:
          description: The build spec declaration to use for the builds in this build project.
          returned: always
          type: str
        auth:
          description: Information about the authorization settings for AWS CodeBuild to access the source code to be built.
          returned: when configured
          type: complex
        insecure_ssl:
          description: True if set to ignore SSL warnings.
          returned: when configured
          type: bool
    artifacts:
      description: Information about the output of build artifacts
      returned: always
      type: complex
      contains:
        type:
          description: The type of build artifact.
          returned: always
          type: str
          sample: CODEPIPELINE
        location:
          description: Output location for build artifacts
          returned: when configured
          type: str
        # and more... see http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html#CodeBuild.Client.create_project
    cache:
      description: Cache settings for the build project.
      returned: when configured
      type: dict
    environment:
      description: Environment settings for the build
      returned: always
      type: dict
    service_role:
      description: IAM role to be used during build to access other AWS services.
      returned: always
      type: str
      sample: arn:aws:iam::123123123:role/codebuild-service-role
    timeout_in_minutes:
      description: The timeout of a build in minutes
      returned: always
      type: int
      sample: 60
    tags:
      description:
        - Tags added to the project in the boto3 list of dictionaries format.
        - I(tags) and I(reource_tags) represent the same information in
          different formats.
      returned: when configured
      type: list
    reource_tags:
      description:
        - A simple dictionary representing the tags added to the project.
        - I(tags) and I(reource_tags) represent the same information in
          different formats.
      returned: when configured
      type: dict
      version_added: 4.0.0
    created:
      description: Timestamp of the create time of the project
      returned: always
      type: str
      sample: "2018-04-17T16:56:03.245000+02:00"
'''

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


def create_or_update_project(client, params, module):
    resp = {}
    name = params['name']
    # clean up params
    formatted_params = snake_dict_to_camel_dict(dict((k, v) for k, v in params.items() if v is not None))
    permitted_create_params = get_boto3_client_method_parameters(client, 'create_project')
    permitted_update_params = get_boto3_client_method_parameters(client, 'update_project')

    formatted_create_params = dict((k, v) for k, v in formatted_params.items() if k in permitted_create_params)
    formatted_update_params = dict((k, v) for k, v in formatted_params.items() if k in permitted_update_params)

    # Check if project with that name already exists and if so update existing:
    found = describe_project(client=client, name=name, module=module)
    changed = False

    if 'name' in found:
        found_project = found
        found_tags = found_project.pop('tags', [])
        # Support tagging using a dict instead of the list of dicts
        if params['resource_tags'] is not None:
            if params['purge_tags']:
                tags = dict()
            else:
                tags = boto3_tag_list_to_ansible_dict(found_tags)
            tags.update(params['resource_tags'])
            formatted_update_params['tags'] = ansible_dict_to_boto3_tag_list(tags, tag_name_key_name='key', tag_value_key_name='value')

        resp = update_project(client=client, params=formatted_update_params, module=module)
        updated_project = resp['project']

        # Prep both dicts for sensible change comparison:
        found_project.pop('lastModified')
        updated_project.pop('lastModified')
        updated_tags = updated_project.pop('tags', [])
        found_project['ResourceTags'] = boto3_tag_list_to_ansible_dict(found_tags)
        updated_project['ResourceTags'] = boto3_tag_list_to_ansible_dict(updated_tags)

        if updated_project != found_project:
            changed = True
        updated_project['tags'] = updated_tags
        return resp, changed
    # Or create new project:
    try:
        if params['source'] is None or params['artifacts'] is None:
            module.fail_json(
                "The source and artifacts parameters must be provided when "
                "creating a new project.  No existing project was found.")
        resp = client.create_project(**formatted_create_params)
        changed = True
        return resp, changed
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to create CodeBuild project")


def update_project(client, params, module):
    name = params['name']

    try:
        resp = client.update_project(**params)
        return resp
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to update CodeBuild project")


def delete_project(client, name, module):
    found = describe_project(client=client, name=name, module=module)
    changed = False
    if 'name' in found:
        # Mark as changed when a project with that name existed before calling delete
        changed = True
    try:
        resp = client.delete_project(name=name)
        return resp, changed
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to delete CodeBuild project")


def describe_project(client, name, module):
    project = {}
    try:
        projects = client.batch_get_projects(names=[name])['projects']
        if len(projects) > 0:
            project = projects[0]
        return project
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to describe CodeBuild projects")


def format_project_result(project_result):
    formated_result = camel_dict_to_snake_dict(project_result)
    project = project_result.get('project', {})
    if project:
        tags = project.get('tags', [])
        formated_result['project']['resource_tags'] = boto3_tag_list_to_ansible_dict(tags)
    formated_result['ORIGINAL'] = project_result
    return formated_result


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        source=dict(type='dict'),
        artifacts=dict(type='dict'),
        cache=dict(type='dict'),
        environment=dict(type='dict'),
        service_role=dict(),
        timeout_in_minutes=dict(type='int', default=60),
        encryption_key=dict(no_log=False),
        tags=dict(type='list', elements='dict'),
        resource_tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=True),
        vpc_config=dict(type='dict'),
        state=dict(choices=['present', 'absent'], default='present')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    client_conn = module.client('codebuild')

    state = module.params.get('state')
    changed = False

    if module.params['tags']:
        module.deprecate(
            'The tags parameter currently uses a non-standard format and has '
            'been deprecated.  In release 6.0.0 this paramater will accept '
            'a simple key/value pair dictionary instead of the current list '
            'of dictionaries.  It is recommended to migrate to using the '
            'resource_tags parameter which already accepts the simple dictionary '
            'format.', version='6.0.0', collection_name='community.aws')

    if state == 'present':
        project_result, changed = create_or_update_project(
            client=client_conn,
            params=module.params,
            module=module)
    elif state == 'absent':
        project_result, changed = delete_project(client=client_conn, name=module.params['name'], module=module)

    formatted_result = format_project_result(project_result)
    module.exit_json(changed=changed, **formatted_result)


if __name__ == '__main__':
    main()
