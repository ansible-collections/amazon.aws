.. _community.aws.cloudformation_stack_set_module:


**************************************
community.aws.cloudformation_stack_set
**************************************

**Manage groups of CloudFormation stacks**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Launches/updates/deletes AWS CloudFormation Stack Sets.



Requirements
------------
The below requirements are needed on the host that executes this module.

- boto
- boto3>=1.6
- botocore>=1.10.26
- python >= 2.6


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>accounts</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of AWS accounts in which to create instance of CloudFormation stacks.</div>
                        <div>At least one region must be specified to create a stack set. On updates, if fewer regions are specified only the specified regions will have their stack instances updated.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>administration_role_arn</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ARN of the administration role, meaning the role that CloudFormation Stack Sets use to assume the roles in your child accounts.</div>
                        <div>This defaults to <code>arn:aws:iam::{{ account ID }}:role/AWSCloudFormationStackSetAdministrationRole</code> where <code>{{ account ID }}</code> is replaced with the account number of the current IAM role/user/STS credentials.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: admin_role_arn, admin_role, administration_role</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_access_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS access key. If not set then the value of the AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY or EC2_ACCESS_KEY environment variable is used.</div>
                        <div>If <em>profile</em> is set this parameter is ignored.</div>
                        <div>Passing the <em>aws_access_key</em> and <em>profile</em> options at the same time has been deprecated and the options will be made mutually exclusive after 2022-06-01.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: ec2_access_key, access_key</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_ca_bundle</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The location of a CA Bundle to use when validating SSL certificates.</div>
                        <div>Only used for boto3 based modules.</div>
                        <div>Note: The CA Bundle is read &#x27;module&#x27; side and may need to be explicitly copied from the controller if not run locally.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A dictionary to modify the botocore configuration.</div>
                        <div>Parameters can be found at <a href='https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config'>https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config</a>.</div>
                        <div>Only the &#x27;user_agent&#x27; key is used for boto modules. See <a href='http://boto.cloudhackers.com/en/latest/boto_config_tut.html#boto'>http://boto.cloudhackers.com/en/latest/boto_config_tut.html#boto</a> for more boto configuration.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_secret_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS secret key. If not set then the value of the AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, or EC2_SECRET_KEY environment variable is used.</div>
                        <div>If <em>profile</em> is set this parameter is ignored.</div>
                        <div>Passing the <em>aws_secret_key</em> and <em>profile</em> options at the same time has been deprecated and the options will be made mutually exclusive after 2022-06-01.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: ec2_secret_key, secret_key</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>capabilities</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>CAPABILITY_IAM</li>
                                    <li>CAPABILITY_NAMED_IAM</li>
                        </ul>
                </td>
                <td>
                        <div>Capabilities allow stacks to create and modify IAM resources, which may include adding users or roles.</div>
                        <div>Currently the only available values are &#x27;CAPABILITY_IAM&#x27; and &#x27;CAPABILITY_NAMED_IAM&#x27;. Either or both may be provided.</div>
                        <div>The following resources require that one or both of these parameters is specified: AWS::IAM::AccessKey, AWS::IAM::Group, AWS::IAM::InstanceProfile, AWS::IAM::Policy, AWS::IAM::Role, AWS::IAM::User, AWS::IAM::UserToGroupAddition</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>debug_botocore_endpoint_logs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Use a botocore.endpoint logger to parse the unique (rather than total) &quot;resource:action&quot; API calls made during a task, outputing the set to the resource_actions key in the task results. Use the aws_resource_action callback to output to total list made during a playbook. The ANSIBLE_DEBUG_BOTOCORE_LOGS environment variable may also be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A description of what this stack set creates.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ec2_url</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Url to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints). Ignored for modules where region is required. Must be specified for all other modules if region is not used. If not set then the value of the EC2_URL environment variable, if any, is used.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_endpoint_url, endpoint_url</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>execution_role_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ARN of the execution role, meaning the role that CloudFormation Stack Sets assumes in your child accounts.</div>
                        <div>This MUST NOT be an ARN, and the roles must exist in each child account specified.</div>
                        <div>The default name for the execution role is <code>AWSCloudFormationStackSetExecutionRole</code></div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: exec_role_name, exec_role, execution_role</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>failure_tolerance</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Settings to change what is considered &quot;failed&quot; when running stack instance updates, and how many to do at a time.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fail_count</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The number of accounts, per region, for which this operation can fail before CloudFormation stops the operation in that region.</div>
                        <div>You must specify one of <em>fail_count</em> and <em>fail_percentage</em>.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fail_percentage</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The percentage of accounts, per region, for which this stack operation can fail before CloudFormation stops the operation in that region.</div>
                        <div>You must specify one of <em>fail_count</em> and <em>fail_percentage</em>.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>parallel_count</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The maximum number of accounts in which to perform this operation at one time.</div>
                        <div><em>parallel_count</em> may be at most one more than the <em>fail_count</em>.</div>
                        <div>You must specify one of <em>parallel_count</em> and <em>parallel_percentage</em>.</div>
                        <div>Note that this setting lets you specify the maximum for operations. For large deployments, under certain circumstances the actual count may be lower.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>parallel_percentage</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The maximum percentage of accounts in which to perform this operation at one time.</div>
                        <div>You must specify one of <em>parallel_count</em> and <em>parallel_percentage</em>.</div>
                        <div>Note that this setting lets you specify the maximum for operations. For large deployments, under certain circumstances the actual percentage may be lower.</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the CloudFormation stack set.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>parameters</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                <td>
                        <div>A list of hashes of all the template variables for the stack. The value can be a string or a dict.</div>
                        <div>Dict can be used to set additional template parameter attributes like UsePreviousValue (see example).</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Uses a boto profile. Only works with boto &gt;= 2.24.0.</div>
                        <div>Using <em>profile</em> will override <em>aws_access_key</em>, <em>aws_secret_key</em> and <em>security_token</em> and support for passing them at the same time as <em>profile</em> has been deprecated.</div>
                        <div><em>aws_access_key</em>, <em>aws_secret_key</em> and <em>security_token</em> will be made mutually exclusive with <em>profile</em> after 2022-06-01.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_profile</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>purge_stacks</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Only applicable when <em>state=absent</em>. Sets whether, when deleting a stack set, the stack instances should also be deleted.</div>
                        <div>By default, instances will be deleted. To keep stacks when stack set is deleted set <em>purge_stacks=false</em>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>region</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The AWS region to use. If not specified then the value of the AWS_REGION or EC2_REGION environment variable, if any, is used. See <a href='http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region'>http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region</a></div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_region, ec2_region</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>regions</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of AWS regions to create instances of a stack in. The <em>region</em> parameter chooses where the Stack Set is created, and <em>regions</em> specifies the region for stack instances.</div>
                        <div>At least one region must be specified to create a stack set. On updates, if fewer regions are specified only the specified regions will have their stack instances updated.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>security_token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS STS security token. If not set then the value of the AWS_SECURITY_TOKEN or EC2_SECURITY_TOKEN environment variable is used.</div>
                        <div>If <em>profile</em> is set this parameter is ignored.</div>
                        <div>Passing the <em>security_token</em> and <em>profile</em> options at the same time has been deprecated and the options will be made mutually exclusive after 2022-06-01.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_security_token, access_token</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>present</b>&nbsp;&larr;</div></li>
                                    <li>absent</li>
                        </ul>
                </td>
                <td>
                        <div>If <em>state=present</em>, stack will be created.  If <em>state=present</em> and if stack exists and template has changed, it will be updated. If <em>state=absent</em>, stack will be removed.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tags</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Dictionary of tags to associate with stack and its resources during stack creation.</div>
                        <div>Can be updated later, updating tags removes previous entries.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The local path of the CloudFormation template.</div>
                        <div>This must be the full path to the file, relative to the working directory. If using roles this may look like <code>roles/cloudformation/files/cloudformation-example.json</code>.</div>
                        <div>If <em>state=present</em> and the stack does not exist yet, either <em>template</em>, <em>template_body</em> or <em>template_url</em> must be specified (but only one of them).</div>
                        <div>If <em>state=present</em>, the stack does exist, and neither <em>template</em>, <em>template_body</em> nor <em>template_url</em> are specified, the previous template will be reused.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>template_body</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Template body. Use this to pass in the actual body of the CloudFormation template.</div>
                        <div>If <em>state=present</em> and the stack does not exist yet, either <em>template</em>, <em>template_body</em> or <em>template_url</em> must be specified (but only one of them).</div>
                        <div>If <em>state=present</em>, the stack does exist, and neither <em>template</em>, <em>template_body</em> nor <em>template_url</em> are specified, the previous template will be reused.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>template_url</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Location of file containing the template body.</div>
                        <div>The URL must point to a template (max size 307,200 bytes) located in an S3 bucket in the same region as the stack.</div>
                        <div>If <em>state=present</em> and the stack does not exist yet, either <em>template</em>, <em>template_body</em> or <em>template_url</em> must be specified (but only one of them).</div>
                        <div>If <em>state=present</em>, the stack does exist, and neither <em>template</em>, <em>template_body</em> nor <em>template_url</em> are specified, the previous template will be reused.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>validate_certs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>When set to &quot;no&quot;, SSL certificates will not be validated for boto versions &gt;= 2.6.0.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>wait</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Whether or not to wait for stack operation to complete. This includes waiting for stack instances to reach UPDATE_COMPLETE status.</div>
                        <div>If you choose not to wait, this module will not notify when stack operations fail because it will not wait for them to finish.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>wait_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">900</div>
                </td>
                <td>
                        <div>How long to wait (in seconds) for stacks to complete create/update/delete operations.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - To make an individual stack, you want the :ref:`amazon.aws.cloudformation <amazon.aws.cloudformation_module>` module.
   - If parameters are not set within the module, the following environment variables can be used in decreasing order of precedence ``AWS_URL`` or ``EC2_URL``, ``AWS_PROFILE`` or ``AWS_DEFAULT_PROFILE``, ``AWS_ACCESS_KEY_ID`` or ``AWS_ACCESS_KEY`` or ``EC2_ACCESS_KEY``, ``AWS_SECRET_ACCESS_KEY`` or ``AWS_SECRET_KEY`` or ``EC2_SECRET_KEY``, ``AWS_SECURITY_TOKEN`` or ``EC2_SECURITY_TOKEN``, ``AWS_REGION`` or ``EC2_REGION``, ``AWS_CA_BUNDLE``
   - Ansible uses the boto configuration file (typically ~/.boto) if no credentials are provided. See https://boto.readthedocs.io/en/latest/boto_config_tut.html
   - ``AWS_REGION`` or ``EC2_REGION`` can be typically be used to specify the AWS region, when required, but this can also be configured in the boto config file



Examples
--------

.. code-block:: yaml

    - name: Create a stack set with instances in two accounts
      community.aws.cloudformation_stack_set:
        name: my-stack
        description: Test stack in two accounts
        state: present
        template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
        accounts: [1234567890, 2345678901]
        regions:
        - us-east-1

    - name: on subsequent calls, templates are optional but parameters and tags can be altered
      community.aws.cloudformation_stack_set:
        name: my-stack
        state: present
        parameters:
          InstanceName: my_stacked_instance
        tags:
          foo: bar
          test: stack
        accounts: [1234567890, 2345678901]
        regions:
        - us-east-1

    - name: The same type of update, but wait for the update to complete in all stacks
      community.aws.cloudformation_stack_set:
        name: my-stack
        state: present
        wait: true
        parameters:
          InstanceName: my_restacked_instance
        tags:
          foo: bar
          test: stack
        accounts: [1234567890, 2345678901]
        regions:
        - us-east-1



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>operations</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>All operations initiated by this run of the cloudformation_stack_set module</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;action&#x27;: &#x27;CREATE&#x27;, &#x27;administration_role_arn&#x27;: &#x27;arn:aws:iam::1234567890:role/AWSCloudFormationStackSetAdministrationRole&#x27;, &#x27;creation_timestamp&#x27;: &#x27;2018-06-18T17:40:46.372000+00:00&#x27;, &#x27;end_timestamp&#x27;: &#x27;2018-06-18T17:41:24.560000+00:00&#x27;, &#x27;execution_role_name&#x27;: &#x27;AWSCloudFormationStackSetExecutionRole&#x27;, &#x27;operation_id&#x27;: &#x27;Ansible-StackInstance-Create-0ff2af5b-251d-4fdb-8b89-1ee444eba8b8&#x27;, &#x27;operation_preferences&#x27;: {&#x27;region_order&#x27;: [&#x27;us-east-1&#x27;, &#x27;us-east-2&#x27;]}, &#x27;stack_set_id&#x27;: &#x27;TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929&#x27;, &#x27;status&#x27;: &#x27;FAILED&#x27;}]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>operations_log</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Most recent events in CloudFormation&#x27;s event log. This may be from a previous run in some cases.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;action&#x27;: &#x27;CREATE&#x27;, &#x27;creation_timestamp&#x27;: &#x27;2018-06-18T17:40:46.372000+00:00&#x27;, &#x27;end_timestamp&#x27;: &#x27;2018-06-18T17:41:24.560000+00:00&#x27;, &#x27;operation_id&#x27;: &#x27;Ansible-StackInstance-Create-0ff2af5b-251d-4fdb-8b89-1ee444eba8b8&#x27;, &#x27;status&#x27;: &#x27;FAILED&#x27;, &#x27;stack_instances&#x27;: [{&#x27;account&#x27;: &#x27;1234567890&#x27;, &#x27;region&#x27;: &#x27;us-east-1&#x27;, &#x27;stack_set_id&#x27;: &#x27;TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929&#x27;, &#x27;status&#x27;: &#x27;OUTDATED&#x27;, &#x27;status_reason&#x27;: &quot;Account 1234567890 should have &#x27;AWSCloudFormationStackSetAdministrationRole&#x27; role with trust relationship to CloudFormation service.&quot;}]}]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>stack_instances</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                    </div>
                </td>
                <td>state == present</td>
                <td>
                            <div>CloudFormation stack instances that are members of this stack set. This will also include their region and account ID.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;account&#x27;: &#x27;1234567890&#x27;, &#x27;region&#x27;: &#x27;us-east-1&#x27;, &#x27;stack_set_id&#x27;: &#x27;TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929&#x27;, &#x27;status&#x27;: &#x27;OUTDATED&#x27;, &#x27;status_reason&#x27;: &quot;Account 1234567890 should have &#x27;AWSCloudFormationStackSetAdministrationRole&#x27; role with trust relationship to CloudFormation service.\n&quot;}, {&#x27;account&#x27;: &#x27;1234567890&#x27;, &#x27;region&#x27;: &#x27;us-east-2&#x27;, &#x27;stack_set_id&#x27;: &#x27;TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929&#x27;, &#x27;status&#x27;: &#x27;OUTDATED&#x27;, &#x27;status_reason&#x27;: &#x27;Cancelled since failure tolerance has exceeded&#x27;}]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>stack_set</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>state == present</td>
                <td>
                            <div>Facts about the currently deployed stack set, its parameters, and its tags</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;administration_role_arn&#x27;: &#x27;arn:aws:iam::1234567890:role/AWSCloudFormationStackSetAdministrationRole&#x27;, &#x27;capabilities&#x27;: [], &#x27;description&#x27;: &#x27;test stack PRIME&#x27;, &#x27;execution_role_name&#x27;: &#x27;AWSCloudFormationStackSetExecutionRole&#x27;, &#x27;parameters&#x27;: [], &#x27;stack_set_arn&#x27;: &#x27;arn:aws:cloudformation:us-east-1:1234567890:stackset/TestStackPrime:19f3f684-aae9-467-ba36-e09f92cf5929&#x27;, &#x27;stack_set_id&#x27;: &#x27;TestStackPrime:19f3f684-aae9-4e67-ba36-e09f92cf5929&#x27;, &#x27;stack_set_name&#x27;: &#x27;TestStackPrime&#x27;, &#x27;status&#x27;: &#x27;ACTIVE&#x27;, &#x27;tags&#x27;: {&#x27;Some&#x27;: &#x27;Thing&#x27;, &#x27;an&#x27;: &#x27;other&#x27;}, &#x27;template_body&#x27;: &#x27;AWSTemplateFormatVersion: &quot;2010-09-09&quot;\nParameters: {}\nResources:\n  Bukkit:\n    Type: &quot;AWS::S3::Bucket&quot;\n    Properties: {}\n  other:\n    Type: &quot;AWS::SNS::Topic&quot;\n    Properties: {}\n&#x27;}</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Ryan Scott Brown (@ryansb)
