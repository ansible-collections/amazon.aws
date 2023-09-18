#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
---
module: codepipeline
version_added: 1.0.0
short_description: Create or delete AWS CodePipelines
notes:
    - For details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/codepipeline.html).
description:
    - Create or delete a CodePipeline on AWS.
    - Prior to release 5.0.0 this module was called C(community.aws.aws_codepipeline).
      The usage did not change.
author:
    - Stefan Horning (@stefanhorning) <horning@mediapeers.com>
options:
    name:
        description:
            - Name of the CodePipeline.
        required: true
        type: str
    role_arn:
        description:
            - ARN of the IAM role to use when executing the CodePipeline.
        required: true
        type: str
    artifact_store:
        description:
            - Location information where artifacts are stored (on S3). Dictionary with fields type and location.
        required: true
        suboptions:
            type:
                description:
                    - Type of the artifacts storage (only 'S3' is currently supported).
                type: str
            location:
                description:
                    - Bucket name for artifacts.
                type: str
        type: dict
    stages:
        description:
            - List of stages to perform in the CodePipeline. List of dictionaries containing name and actions for each stage.
        required: true
        suboptions:
            name:
                description:
                    - Name of the stage (step) in the CodePipeline.
                type: str
            actions:
                description:
                    - List of action configurations for that stage.
                    - 'See the boto3 documentation for full documentation of suboptions:'
                    - 'U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codepipeline.html#CodePipeline.Client.create_pipeline)'
                type: list
                elements: dict
        elements: dict
        type: list
    version:
        description:
            - Version number of the CodePipeline. This number is automatically incremented when a CodePipeline is updated.
        required: false
        type: int
    state:
        description:
            - Create or remove CodePipeline.
        default: 'present'
        choices: ['present', 'absent']
        type: str
extends_documentation_fragment:
    - amazon.aws.aws
    - amazon.aws.ec2
    - amazon.aws.boto3
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Example for creating a pipeline for continuous deploy of Github code to an ECS cluster (container)
- community.aws.aws_codepipeline:
    name: my_deploy_pipeline
    role_arn: arn:aws:iam::123456:role/AWS-CodePipeline-Service
    artifact_store:
      type: S3
      location: my_s3_codepipline_bucket
    stages:
      - name: Get_source
        actions:
          -
            name: Git_pull
            actionTypeId:
              category: Source
              owner: ThirdParty
              provider: GitHub
              version: '1'
            outputArtifacts:
              - { name: my-app-source }
            configuration:
              Owner: mediapeers
              Repo: my_gh_repo
              PollForSourceChanges: 'true'
              Branch: master
              # Generate token like this:
              # https://docs.aws.amazon.com/codepipeline/latest/userguide/GitHub-rotate-personal-token-CLI.html
              # GH Link: https://github.com/settings/tokens
              OAuthToken: 'abc123def456'
            runOrder: 1
      - name: Build
        actions:
          -
            name: CodeBuild
            actionTypeId:
              category: Build
              owner: AWS
              provider: CodeBuild
              version: '1'
            inputArtifacts:
              - { name: my-app-source }
            outputArtifacts:
              - { name: my-app-build }
            configuration:
              # A project with that name needs to be setup on AWS CodeBuild already (use code_build module).
              ProjectName: codebuild-project-name
            runOrder: 1
      - name: ECS_deploy
        actions:
          -
            name: ECS_deploy
            actionTypeId:
              category: Deploy
              owner: AWS
              provider: ECS
              version: '1'
            inputArtifacts:
              - { name: vod-api-app-build }
            configuration:
              # an ECS cluster with that name needs to be setup on AWS ECS already (use ecs_cluster and ecs_service module)
              ClusterName: ecs-cluster-name
              ServiceName: ecs-cluster-service-name
              FileName: imagedefinitions.json
    region: us-east-1
    state: present
'''

RETURN = r'''
pipeline:
  description: Returns the dictionary describing the CodePipeline configuration.
  returned: success
  type: complex
  contains:
    name:
      description: Name of the CodePipeline
      returned: always
      type: str
      sample: my_deploy_pipeline
    role_arn:
      description: ARN of the IAM role attached to the CodePipeline
      returned: always
      type: str
      sample: arn:aws:iam::123123123:role/codepipeline-service-role
    artifact_store:
      description: Information about where the build artifacts are stored
      returned: always
      type: complex
      contains:
        type:
          description: The type of the artifacts store, such as S3
          returned: always
          type: str
          sample: S3
        location:
          description: The location of the artifacts storage (s3 bucket name)
          returned: always
          type: str
          sample: my_s3_codepipline_bucket
        encryption_key:
          description: The encryption key used to encrypt the artifacts store, such as an AWS KMS key.
          returned: when configured
          type: str
    stages:
      description: List of stages configured for this CodePipeline
      returned: always
      type: list
    version:
      description:
        - The version number of the CodePipeline.
        - This number is auto incremented when CodePipeline params are changed.
      returned: always
      type: int
'''

import copy

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_policies


def create_pipeline(client, name, role_arn, artifact_store, stages, version, module):
    pipeline_dict = {'name': name, 'roleArn': role_arn, 'artifactStore': artifact_store, 'stages': stages}
    if version:
        pipeline_dict['version'] = version
    try:
        resp = client.create_pipeline(pipeline=pipeline_dict)
        return resp
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable create pipeline {0}".format(pipeline_dict['name']))


def update_pipeline(client, pipeline_dict, module):
    try:
        resp = client.update_pipeline(pipeline=pipeline_dict)
        return resp
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable update pipeline {0}".format(pipeline_dict['name']))


def delete_pipeline(client, name, module):
    try:
        resp = client.delete_pipeline(name=name)
        return resp
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable delete pipeline {0}".format(name))


def describe_pipeline(client, name, version, module):
    pipeline = {}
    try:
        if version is not None:
            pipeline = client.get_pipeline(name=name, version=version)
            return pipeline
        else:
            pipeline = client.get_pipeline(name=name)
            return pipeline
    except is_boto3_error_code('PipelineNotFoundException'):
        return pipeline
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        role_arn=dict(required=True, type='str'),
        artifact_store=dict(required=True, type='dict'),
        stages=dict(required=True, type='list', elements='dict'),
        version=dict(type='int'),
        state=dict(choices=['present', 'absent'], default='present')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    client_conn = module.client('codepipeline')

    state = module.params.get('state')
    changed = False

    # Determine if the CodePipeline exists
    found_code_pipeline = describe_pipeline(client=client_conn, name=module.params['name'], version=module.params['version'], module=module)
    pipeline_result = {}

    if state == 'present':
        if 'pipeline' in found_code_pipeline:
            pipeline_dict = copy.deepcopy(found_code_pipeline['pipeline'])
            # Update dictionary with provided module params:
            pipeline_dict['roleArn'] = module.params['role_arn']
            pipeline_dict['artifactStore'] = module.params['artifact_store']
            pipeline_dict['stages'] = module.params['stages']
            if module.params['version'] is not None:
                pipeline_dict['version'] = module.params['version']

            pipeline_result = update_pipeline(client=client_conn, pipeline_dict=pipeline_dict, module=module)

            if compare_policies(found_code_pipeline['pipeline'], pipeline_result['pipeline']):
                changed = True
        else:
            pipeline_result = create_pipeline(
                client=client_conn,
                name=module.params['name'],
                role_arn=module.params['role_arn'],
                artifact_store=module.params['artifact_store'],
                stages=module.params['stages'],
                version=module.params['version'],
                module=module)
            changed = True
    elif state == 'absent':
        if found_code_pipeline:
            pipeline_result = delete_pipeline(client=client_conn, name=module.params['name'], module=module)
            changed = True

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(pipeline_result))


if __name__ == '__main__':
    main()
