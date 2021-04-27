.. _amazon.aws.cloudformation_module:


*************************
amazon.aws.cloudformation
*************************

**Create or delete an AWS CloudFormation stack**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Launches or updates an AWS CloudFormation stack and waits for it complete.



Requirements
------------
The below requirements are needed on the host that executes this module.

- boto
- boto3
- botocore>=1.5.45
- python >= 2.6


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
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
                <td colspan="1">
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
                <td colspan="1">
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
                <td colspan="1">
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
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>backoff_delay</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">3</div>
                </td>
                <td>
                        <div>Number of seconds to wait for the next retry.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>backoff_max_delay</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">30</div>
                </td>
                <td>
                        <div>Maximum amount of time to wait between retries.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>backoff_retries</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">10</div>
                </td>
                <td>
                        <div>Number of times to retry operation.</div>
                        <div>AWS API throttling mechanism fails CloudFormation module so we have to retry a couple of times.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>capabilities</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]</div>
                </td>
                <td>
                        <div>Specify capabilities that stack template contains.</div>
                        <div>Valid values are <code>CAPABILITY_IAM</code>, <code>CAPABILITY_NAMED_IAM</code> and <code>CAPABILITY_AUTO_EXPAND</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>changeset_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name given to the changeset when creating a changeset.</div>
                        <div>Only used when <em>create_changeset=true</em>.</div>
                        <div>By default a name prefixed with Ansible-STACKNAME is generated based on input parameters. See the AWS Change Sets docs for more information <a href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html'>https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html</a></div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>create_changeset</b>
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
                        <div>If stack already exists create a changeset instead of directly applying changes.  See the AWS Change Sets docs <a href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html'>https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html</a>.</div>
                        <div>WARNING: if the stack does not exist, it will be created without changeset. If <em>state=absent</em>, the stack will be deleted immediately with no changeset.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>create_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The amount of time (in minutes) that can pass before the stack status becomes CREATE_FAILED</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_rollback</b>
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
                        <div>If a stacks fails to form, rollback will remove the stack.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>events_limit</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">200</div>
                </td>
                <td>
                        <div>Maximum number of CloudFormation events to fetch from a stack when creating or updating it.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>notification_arns</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A comma separated list of Simple Notification Service (SNS) topic ARNs to publish stack related events.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>on_create_failure</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>DO_NOTHING</li>
                                    <li>ROLLBACK</li>
                                    <li>DELETE</li>
                        </ul>
                </td>
                <td>
                        <div>Action to take upon failure of stack creation. Incompatible with the <em>disable_rollback</em> option.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
                <td colspan="1">
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
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>role_arn</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The role that AWS CloudFormation assumes to create the stack. See the AWS CloudFormation Service Role docs <a href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html'>https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html</a></div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>stack_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the CloudFormation stack.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>stack_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The path of the file containing the CloudFormation stack policy. A policy cannot be removed once placed, but it can be modified. for instance, allow all updates <a href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html#d0e9051'>https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html#d0e9051</a></div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>stack_policy_body</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">json</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.5.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The CloudFormation stack policy in JSON. A policy cannot be removed once placed, but it can be modified. for instance, allow all updates <a href='https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html#d0e9051'>https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html#d0e9051</a></div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>stack_policy_on_update_body</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">json</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.5.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>the body of the cloudformation stack policy only applied during this update.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
                        <div>If <em>state=present</em>, stack will be created.</div>
                        <div>If <em>state=present</em> and if stack exists and template has changed, it will be updated.</div>
                        <div>If <em>state=absent</em>, stack will be removed.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
                <td colspan="1">
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
                <td colspan="1">
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
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>template_format</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>This parameter is ignored since Ansible 2.3 and will be removed after 2022-06-01.</div>
                        <div>Templates are now passed raw to CloudFormation regardless of format.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>template_parameters</b>
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
                <td colspan="1">
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
                        <div>Location of file containing the template body. The URL must point to a template (max size 307,200 bytes) located in an S3 bucket in the same region as the stack.</div>
                        <div>If <em>state=present</em> and the stack does not exist yet, either <em>template</em>, <em>template_body</em> or <em>template_url</em> must be specified (but only one of them).</div>
                        <div>If <em>state=present</em>, the stack does exist, and neither <em>template</em>, <em>template_body</em> nor <em>template_url</em> are specified, the previous template will be reused.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>termination_protection</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Enable or disable termination protection on the stack. Only works with botocore &gt;= 1.7.18.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
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
    </table>
    <br/>


Notes
-----

.. note::
   - CloudFormation features change often, and this module tries to keep up. That means your botocore version should be fresh. The version listed in the requirements is the oldest version that works with the module as a whole. Some features may require recent versions, and we do not pinpoint a minimum version for each feature. Instead of relying on the minimum version, keep botocore up to date. AWS is always releasing features and fixing bugs.
   - If parameters are not set within the module, the following environment variables can be used in decreasing order of precedence ``AWS_URL`` or ``EC2_URL``, ``AWS_PROFILE`` or ``AWS_DEFAULT_PROFILE``, ``AWS_ACCESS_KEY_ID`` or ``AWS_ACCESS_KEY`` or ``EC2_ACCESS_KEY``, ``AWS_SECRET_ACCESS_KEY`` or ``AWS_SECRET_KEY`` or ``EC2_SECRET_KEY``, ``AWS_SECURITY_TOKEN`` or ``EC2_SECURITY_TOKEN``, ``AWS_REGION`` or ``EC2_REGION``, ``AWS_CA_BUNDLE``
   - Ansible uses the boto configuration file (typically ~/.boto) if no credentials are provided. See https://boto.readthedocs.io/en/latest/boto_config_tut.html
   - ``AWS_REGION`` or ``EC2_REGION`` can be typically be used to specify the AWS region, when required, but this can also be configured in the boto config file



Examples
--------

.. code-block:: yaml

    - name: create a cloudformation stack
      amazon.aws.cloudformation:
        stack_name: "ansible-cloudformation"
        state: "present"
        region: "us-east-1"
        disable_rollback: true
        template: "files/cloudformation-example.json"
        template_parameters:
          KeyName: "jmartin"
          DiskType: "ephemeral"
          InstanceType: "m1.small"
          ClusterSize: 3
        tags:
          Stack: "ansible-cloudformation"

    # Basic role example
    - name: create a stack, specify role that cloudformation assumes
      amazon.aws.cloudformation:
        stack_name: "ansible-cloudformation"
        state: "present"
        region: "us-east-1"
        disable_rollback: true
        template: "roles/cloudformation/files/cloudformation-example.json"
        role_arn: 'arn:aws:iam::123456789012:role/cloudformation-iam-role'

    - name: delete a stack
      amazon.aws.cloudformation:
        stack_name: "ansible-cloudformation-old"
        state: "absent"

    # Create a stack, pass in template from a URL, disable rollback if stack creation fails,
    # pass in some parameters to the template, provide tags for resources created
    - name: create a stack, pass in the template via an URL
      amazon.aws.cloudformation:
        stack_name: "ansible-cloudformation"
        state: present
        region: us-east-1
        disable_rollback: true
        template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
        template_parameters:
          KeyName: jmartin
          DiskType: ephemeral
          InstanceType: m1.small
          ClusterSize: 3
        tags:
          Stack: ansible-cloudformation

    # Create a stack, passing in template body using lookup of Jinja2 template, disable rollback if stack creation fails,
    # pass in some parameters to the template, provide tags for resources created
    - name: create a stack, pass in the template body via lookup template
      amazon.aws.cloudformation:
        stack_name: "ansible-cloudformation"
        state: present
        region: us-east-1
        disable_rollback: true
        template_body: "{{ lookup('template', 'cloudformation.j2') }}"
        template_parameters:
          KeyName: jmartin
          DiskType: ephemeral
          InstanceType: m1.small
          ClusterSize: 3
        tags:
          Stack: ansible-cloudformation

    # Pass a template parameter which uses CloudFormation's UsePreviousValue attribute
    # When use_previous_value is set to True, the given value will be ignored and
    # CloudFormation will use the value from a previously submitted template.
    # If use_previous_value is set to False (default) the given value is used.
    - amazon.aws.cloudformation:
        stack_name: "ansible-cloudformation"
        state: "present"
        region: "us-east-1"
        template: "files/cloudformation-example.json"
        template_parameters:
          DBSnapshotIdentifier:
            use_previous_value: True
            value: arn:aws:rds:es-east-1:000000000000:snapshot:rds:my-db-snapshot
          DBName:
            use_previous_value: True
        tags:
          Stack: "ansible-cloudformation"

    # Enable termination protection on a stack.
    # If the stack already exists, this will update its termination protection
    - name: enable termination protection during stack creation
      amazon.aws.cloudformation:
        stack_name: my_stack
        state: present
        template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
        termination_protection: yes

    # Configure TimeoutInMinutes before the stack status becomes CREATE_FAILED
    # In this case, if disable_rollback is not set or is set to false, the stack will be rolled back.
    - name: enable termination protection during stack creation
      amazon.aws.cloudformation:
        stack_name: my_stack
        state: present
        template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
        create_timeout: 5

    # Configure rollback behaviour on the unsuccessful creation of a stack allowing
    # CloudFormation to clean up, or do nothing in the event of an unsuccessful
    # deployment
    # In this case, if on_create_failure is set to "DELETE", it will clean up the stack if
    # it fails to create
    - name: create stack which will delete on creation failure
      amazon.aws.cloudformation:
        stack_name: my_stack
        state: present
        template_url: https://s3.amazonaws.com/my-bucket/cloudformation.template
        on_create_failure: DELETE



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
                    <b>change_set_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td><em>state=present</em> and <em>create_changeset=true</em></td>
                <td>
                            <div>The ID of the stack change set if one was created</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">arn:aws:cloudformation:us-east-1:012345678901:changeSet/Ansible-StackName-f4496805bd1b2be824d1e315c6884247ede41eb0</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>events</b>
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
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[&#x27;StackEvent AWS::CloudFormation::Stack stackname UPDATE_COMPLETE&#x27;, &#x27;StackEvent AWS::CloudFormation::Stack stackname UPDATE_COMPLETE_CLEANUP_IN_PROGRESS&#x27;]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>log</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Debugging logs. Useful when modifying or finding an error.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[&#x27;updating stack&#x27;]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>stack_outputs</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>state == present</td>
                <td>
                            <div>A key:value dictionary of all the stack outputs currently defined. If there are no stack outputs, it is an empty dictionary.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;MySg&#x27;: &#x27;AnsibleModuleTestYAML-CFTestSg-C8UVS567B6NS&#x27;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>stack_resources</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                    </div>
                </td>
                <td>state == present</td>
                <td>
                            <div>AWS stack resources and their status. List of dictionaries, one dict per resource.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;last_updated_time&#x27;: &#x27;2016-10-11T19:40:14.979000+00:00&#x27;, &#x27;logical_resource_id&#x27;: &#x27;CFTestSg&#x27;, &#x27;physical_resource_id&#x27;: &#x27;cloudformation2-CFTestSg-16UQ4CYQ57O9F&#x27;, &#x27;resource_type&#x27;: &#x27;AWS::EC2::SecurityGroup&#x27;, &#x27;status&#x27;: &#x27;UPDATE_COMPLETE&#x27;, &#x27;status_reason&#x27;: None}]</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- James S. Martin (@jsmartin)
