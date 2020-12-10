.. _amazon.aws.ec2_module:


**************
amazon.aws.ec2
**************

**create, terminate, start or stop an instance in ec2**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Creates or terminates ec2 instances.
- Note: This module uses the older boto Python module to interact with the EC2 API. :ref:`amazon.aws.ec2 <amazon.aws.ec2_module>` will still receive bug fixes, but no new features. Consider using the :ref:`amazon.aws.ec2_instance <amazon.aws.ec2_instance_module>` module instead. If :ref:`amazon.aws.ec2_instance <amazon.aws.ec2_instance_module>` does not support a feature you need that is available in :ref:`amazon.aws.ec2 <amazon.aws.ec2_module>`, please file a feature request.




Requirements
------------
The below requirements are needed on the host that executes this module.

- python >= 2.6
- boto


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
                    <b>assign_public_ip</b>
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
                        <div>When provisioning within vpc, assign a public IP address. Boto library must be 2.13.0+.</div>
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
                    <b>count</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">1</div>
                </td>
                <td>
                        <div>Number of instances to launch.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>count_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">raw</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Used with <em>exact_count</em> to determine how many nodes based on a specific tag criteria should be running. This can be expressed in multiple ways and is shown in the EXAMPLES section.  For instance, one can request 25 servers that are tagged with <code>class=webserver</code>. The specified tag must already exist or be passed in as the <em>instance_tags</em> option.</div>
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
                    <b>ebs_optimized</b>
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
                        <div>Whether instance is using optimized EBS volumes, see <a href='https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html'>https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html</a>.</div>
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
                    <b>exact_count</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>An integer value which indicates how many instances that match the &#x27;count_tag&#x27; parameter should be running. Instances are either created or terminated based on this value.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Security group (or list of groups) to use with the instance.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: groups</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Security group id (or list of ids) to use with the instance.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Identifier for this instance or set of instances, so that the module will be idempotent with respect to EC2 instances.</div>
                        <div>This identifier is valid for at least 24 hours after the termination of the instance, and should not be reused for another call later on.</div>
                        <div>For details, see the description of client token at <a href='https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html'>https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html</a>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>image</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div><em>ami</em> ID to use for the instance.</div>
                        <div>Required when <em>state=present</em>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instance_ids</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>list of instance ids, currently used for states: absent, running, stopped</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: instance_id</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instance_initiated_shutdown_behavior</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>stop</b>&nbsp;&larr;</div></li>
                                    <li>terminate</li>
                        </ul>
                </td>
                <td>
                        <div>Set whether AWS will Stop or Terminate an instance on shutdown. This parameter is ignored when using instance-store. images (which require termination on shutdown).</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instance_profile_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the IAM instance profile (i.e. what the EC2 console refers to as an &quot;IAM Role&quot;) to use. Boto library must be 2.5.0+.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instance_tags</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A hash/dictionary of tags to add to the new instance or for instances to start/stop by tag.  For example <code>{&quot;key&quot;:&quot;value&quot;}</code> or <code>{&quot;key&quot;:&quot;value&quot;,&quot;key2&quot;:&quot;value2&quot;}</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instance_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Instance type to use for the instance, see <a href='https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html'>https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html</a>.</div>
                        <div>Required when creating a new instance.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: type</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kernel</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Kernel eki to use for the instance.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>key_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Key pair to use on the instance.</div>
                        <div>The SSH key must already exist in AWS in order to use this argument.</div>
                        <div>Keys can be created / deleted using the <span class='module'>amazon.aws.ec2_key</span> module.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: keypair</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>monitoring</b>
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
                        <div>Enable detailed monitoring (CloudWatch) for the instance.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>network_interfaces</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of existing network interfaces to attach to the instance at launch. When specifying existing network interfaces, none of the <em>assign_public_ip</em>, <em>private_ip</em>, <em>vpc_subnet_id</em>, <em>group</em>, or <em>group_id</em> parameters may be used. (Those parameters are for creating a new network interface at launch.)</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: network_interface</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>placement_group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Placement group for the instance when using EC2 Clustered Compute.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>private_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The private ip address to assign the instance (from the vpc subnet).</div>
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
                    <b>ramdisk</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Ramdisk eri to use for the instance.</div>
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
                    <b>source_dest_check</b>
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
                        <div>Enable or Disable the Source/Destination checks (for NAT instances and Virtual Routers). When initially creating an instance the EC2 API defaults this to <code>True</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>spot_launch_group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Launch group for spot requests, see <a href='https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-spot-instances-work.html#spot-launch-group'>https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-spot-instances-work.html#spot-launch-group</a>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>spot_price</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Maximum spot price to bid. If not set, a regular on-demand instance is requested.</div>
                        <div>A spot request is made with this maximum bid. When it is filled, the instance is started.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>spot_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>one-time</b>&nbsp;&larr;</div></li>
                                    <li>persistent</li>
                        </ul>
                </td>
                <td>
                        <div>The type of spot request.</div>
                        <div>After being interrupted a <code>persistent</code> spot instance will be started once there is capacity to fill the request again.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>spot_wait_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">600</div>
                </td>
                <td>
                        <div>How long to wait for the spot instance request to be fulfilled. Affects &#x27;Request valid until&#x27; for setting spot request lifespan.</div>
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
                                    <li>absent</li>
                                    <li><div style="color: blue"><b>present</b>&nbsp;&larr;</div></li>
                                    <li>restarted</li>
                                    <li>running</li>
                                    <li>stopped</li>
                        </ul>
                </td>
                <td>
                        <div>Create, terminate, start, stop or restart instances. The state &#x27;restarted&#x27; was added in Ansible 2.2.</div>
                        <div>When <em>state=absent</em>, <em>instance_ids</em> is required.</div>
                        <div>When <em>state=running</em>, <em>state=stopped</em> or <em>state=restarted</em> then either <em>instance_ids</em> or <em>instance_tags</em> is required.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tenancy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>default</b>&nbsp;&larr;</div></li>
                                    <li>dedicated</li>
                        </ul>
                </td>
                <td>
                        <div>An instance with a tenancy of <code>dedicated</code> runs on single-tenant hardware and can only be launched into a VPC.</div>
                        <div>Note that to use dedicated tenancy you MUST specify a <em>vpc_subnet_id</em> as well.</div>
                        <div>Dedicated tenancy is not available for EC2 &quot;micro&quot; instances.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
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
                        <div>Enable or Disable the Termination Protection.</div>
                        <div>Defaults to <code>false</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>user_data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Opaque blob of data which is made available to the EC2 instance.</div>
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
                    <b>volumes</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of hash/dictionaries of volumes to add to the new instance.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>delete_on_termination</b>
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
                        <div>Whether the volume should be automatically deleted when the instance is terminated.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>device_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A name for the device (For example <code>/dev/sda</code>).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>encrypted</b>
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
                        <div>Whether the volume should be encrypted using the &#x27;aws/ebs&#x27; KMS CMK.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ephemeral</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Whether the volume should be ephemeral.</div>
                        <div>Data on ephemeral volumes is lost when the instance is stopped.</div>
                        <div>Mutually exclusive with the <em>snapshot</em> parameter.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>iops</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The number of IOPS per second to provision for the volume.</div>
                        <div>Required when <em>volume_type=io1</em>.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>snapshot</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The ID of an EBS snapshot to copy when creating the volume.</div>
                        <div>Mutually exclusive with the <em>ephemeral</em> parameter.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>volume_size</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The size of the volume (in GiB).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>volume_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The type of volume to create.</div>
                        <div>See <a href='https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumeTypes.html'>https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumeTypes.html</a> for more information on the available volume types.</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vpc_subnet_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The subnet ID in which to launch the instance (VPC).</div>
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
                        <div>Wait for the instance to reach its desired state before returning.</div>
                        <div>Does not wait for SSH, see the &#x27;wait_for_connection&#x27; example for details.</div>
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
                        <b>Default:</b><br/><div style="color: blue">300</div>
                </td>
                <td>
                        <div>How long before wait gives up, in seconds.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>zone</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS availability zone in which to launch the instance.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_zone, ec2_zone</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - If parameters are not set within the module, the following environment variables can be used in decreasing order of precedence ``AWS_URL`` or ``EC2_URL``, ``AWS_PROFILE`` or ``AWS_DEFAULT_PROFILE``, ``AWS_ACCESS_KEY_ID`` or ``AWS_ACCESS_KEY`` or ``EC2_ACCESS_KEY``, ``AWS_SECRET_ACCESS_KEY`` or ``AWS_SECRET_KEY`` or ``EC2_SECRET_KEY``, ``AWS_SECURITY_TOKEN`` or ``EC2_SECURITY_TOKEN``, ``AWS_REGION`` or ``EC2_REGION``, ``AWS_CA_BUNDLE``
   - Ansible uses the boto configuration file (typically ~/.boto) if no credentials are provided. See https://boto.readthedocs.io/en/latest/boto_config_tut.html
   - ``AWS_REGION`` or ``EC2_REGION`` can be typically be used to specify the AWS region, when required, but this can also be configured in the boto config file



Examples
--------

.. code-block:: yaml

    # Note: These examples do not set authentication details, see the AWS Guide for details.

    # Basic provisioning example
    - amazon.aws.ec2:
        key_name: mykey
        instance_type: t2.micro
        image: ami-123456
        wait: yes
        group: webserver
        count: 3
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    # Advanced example with tagging and CloudWatch
    - amazon.aws.ec2:
        key_name: mykey
        group: databases
        instance_type: t2.micro
        image: ami-123456
        wait: yes
        wait_timeout: 500
        count: 5
        instance_tags:
           db: postgres
        monitoring: yes
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    # Single instance with additional IOPS volume from snapshot and volume delete on termination
    - amazon.aws.ec2:
        key_name: mykey
        group: webserver
        instance_type: c3.medium
        image: ami-123456
        wait: yes
        wait_timeout: 500
        volumes:
          - device_name: /dev/sdb
            snapshot: snap-abcdef12
            volume_type: io1
            iops: 1000
            volume_size: 100
            delete_on_termination: true
        monitoring: yes
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    # Single instance with ssd gp2 root volume
    - amazon.aws.ec2:
        key_name: mykey
        group: webserver
        instance_type: c3.medium
        image: ami-123456
        wait: yes
        wait_timeout: 500
        volumes:
          - device_name: /dev/xvda
            volume_type: gp2
            volume_size: 8
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes
        count_tag:
          Name: dbserver
        exact_count: 1

    # Multiple groups example
    - amazon.aws.ec2:
        key_name: mykey
        group: ['databases', 'internal-services', 'sshable', 'and-so-forth']
        instance_type: m1.large
        image: ami-6e649707
        wait: yes
        wait_timeout: 500
        count: 5
        instance_tags:
            db: postgres
        monitoring: yes
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    # Multiple instances with additional volume from snapshot
    - amazon.aws.ec2:
        key_name: mykey
        group: webserver
        instance_type: m1.large
        image: ami-6e649707
        wait: yes
        wait_timeout: 500
        count: 5
        volumes:
        - device_name: /dev/sdb
          snapshot: snap-abcdef12
          volume_size: 10
        monitoring: yes
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    # Dedicated tenancy example
    - amazon.aws.ec2:
        assign_public_ip: yes
        group_id: sg-1dc53f72
        key_name: mykey
        image: ami-6e649707
        instance_type: m1.small
        tenancy: dedicated
        vpc_subnet_id: subnet-29e63245
        wait: yes

    # Spot instance example
    - amazon.aws.ec2:
        spot_price: 0.24
        spot_wait_timeout: 600
        keypair: mykey
        group_id: sg-1dc53f72
        instance_type: m1.small
        image: ami-6e649707
        wait: yes
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes
        spot_launch_group: report_generators
        instance_initiated_shutdown_behavior: terminate

    # Examples using pre-existing network interfaces
    - amazon.aws.ec2:
        key_name: mykey
        instance_type: t2.small
        image: ami-f005ba11
        network_interface: eni-deadbeef

    - amazon.aws.ec2:
        key_name: mykey
        instance_type: t2.small
        image: ami-f005ba11
        network_interfaces: ['eni-deadbeef', 'eni-5ca1ab1e']

    # Launch instances, runs some tasks
    # and then terminate them

    - name: Create a sandbox instance
      hosts: localhost
      gather_facts: False
      vars:
        keypair: my_keypair
        instance_type: m1.small
        security_group: my_securitygroup
        image: my_ami_id
        region: us-east-1
      tasks:
        - name: Launch instance
          amazon.aws.ec2:
             key_name: "{{ keypair }}"
             group: "{{ security_group }}"
             instance_type: "{{ instance_type }}"
             image: "{{ image }}"
             wait: true
             region: "{{ region }}"
             vpc_subnet_id: subnet-29e63245
             assign_public_ip: yes
          register: ec2

        - name: Add new instance to host group
          add_host:
            hostname: "{{ item.public_ip }}"
            groupname: launched
          loop: "{{ ec2.instances }}"

        - name: Wait for SSH to come up
          delegate_to: "{{ item.public_dns_name }}"
          wait_for_connection:
            delay: 60
            timeout: 320
          loop: "{{ ec2.instances }}"

    - name: Configure instance(s)
      hosts: launched
      become: True
      gather_facts: True
      roles:
        - my_awesome_role
        - my_awesome_test

    - name: Terminate instances
      hosts: localhost
      tasks:
        - name: Terminate instances that were previously launched
          amazon.aws.ec2:
            state: 'absent'
            instance_ids: '{{ ec2.instance_ids }}'

    # Start a few existing instances, run some tasks
    # and stop the instances

    - name: Start sandbox instances
      hosts: localhost
      gather_facts: false
      vars:
        instance_ids:
          - 'i-xxxxxx'
          - 'i-xxxxxx'
          - 'i-xxxxxx'
        region: us-east-1
      tasks:
        - name: Start the sandbox instances
          amazon.aws.ec2:
            instance_ids: '{{ instance_ids }}'
            region: '{{ region }}'
            state: running
            wait: True
            vpc_subnet_id: subnet-29e63245
            assign_public_ip: yes
      roles:
        - do_neat_stuff
        - do_more_neat_stuff

    - name: Stop sandbox instances
      hosts: localhost
      gather_facts: false
      vars:
        instance_ids:
          - 'i-xxxxxx'
          - 'i-xxxxxx'
          - 'i-xxxxxx'
        region: us-east-1
      tasks:
        - name: Stop the sandbox instances
          amazon.aws.ec2:
            instance_ids: '{{ instance_ids }}'
            region: '{{ region }}'
            state: stopped
            wait: True
            vpc_subnet_id: subnet-29e63245
            assign_public_ip: yes

    #
    # Start stopped instances specified by tag
    #
    - amazon.aws.ec2:
        instance_tags:
            Name: ExtraPower
        state: running

    #
    # Restart instances specified by tag
    #
    - amazon.aws.ec2:
        instance_tags:
            Name: ExtraPower
        state: restarted

    #
    # Enforce that 5 instances with a tag "foo" are running
    # (Highly recommended!)
    #

    - amazon.aws.ec2:
        key_name: mykey
        instance_type: c1.medium
        image: ami-40603AD1
        wait: yes
        group: webserver
        instance_tags:
            foo: bar
        exact_count: 5
        count_tag: foo
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    #
    # Enforce that 5 running instances named "database" with a "dbtype" of "postgres"
    #

    - amazon.aws.ec2:
        key_name: mykey
        instance_type: c1.medium
        image: ami-40603AD1
        wait: yes
        group: webserver
        instance_tags:
            Name: database
            dbtype: postgres
        exact_count: 5
        count_tag:
            Name: database
            dbtype: postgres
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

    #
    # count_tag complex argument examples
    #

        # instances with tag foo
    - amazon.aws.ec2:
        count_tag:
            foo:

        # instances with tag foo=bar
    - amazon.aws.ec2:
        count_tag:
            foo: bar

        # instances with tags foo=bar & baz
    - amazon.aws.ec2:
        count_tag:
            foo: bar
            baz:

        # instances with tags foo & bar & baz=bang
    - amazon.aws.ec2:
        count_tag:
            - foo
            - bar
            - baz: bang




Status
------


Authors
~~~~~~~

- Tim Gerla (@tgerla)
- Lester Wade (@lwade)
- Seth Vidal (@skvidal)
