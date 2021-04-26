.. _amazon.aws.ec2_metadata_facts_module:


*****************************
amazon.aws.ec2_metadata_facts
*****************************

**gathers facts (instance metadata) about remote hosts within EC2**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- This module fetches data from the instance metadata endpoint in EC2 as per https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html.
- The module must be called from within the EC2 instance itself.
- The module is configured to utilize the session oriented Instance Metadata Service v2 (IMDSv2) https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html.
- If the HttpEndpoint parameter https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_ModifyInstanceMetadataOptions.html#API_ModifyInstanceMetadataOptions_RequestParameters is set to disabled for the EC2 instance, the module will return an error while retrieving a session token.





Notes
-----

.. note::
   - Parameters to filter on ec2_metadata_facts may be added later.



Examples
--------

.. code-block:: yaml

    # Gather EC2 metadata facts
    - amazon.aws.ec2_metadata_facts:

    - debug:
        msg: "This instance is a t1.micro"
      when: ansible_ec2_instance_type == "t1.micro"


Returned Facts
--------------
Facts returned by this module are added/updated in the ``hostvars`` host facts and can be referenced by name just like any other host fact. They do not need to be registered in order to use them.

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <tr>
            <th colspan="2">Fact</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_ami_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The AMI ID used to launch the instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ami-XXXXXXXX</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_ami_launch_index</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>If you started more than one instance at the same time, this value indicates the order in which the instance was launched.
                            </div>
                            <div>The value of the first instance launched is 0.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">0</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_ami_manifest_path</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The path to the AMI manifest file in Amazon S3.
                            </div>
                            <div>If you used an Amazon EBS-backed AMI to launch the instance, the returned result is unknown.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">(unknown)</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_ancestor_ami_ids</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The AMI IDs of any instances that were rebundled to create this AMI.
                            </div>
                            <div>This value will only exist if the AMI manifest file contained an ancestor-amis key.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">(unknown)</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_block_device_mapping_ami</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The virtual device that contains the root/boot file system.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">/dev/sda1</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_block_device_mapping_ebsN</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The virtual devices associated with Amazon EBS volumes, if any are present.
                            </div>
                            <div>Amazon EBS volumes are only available in metadata if they were present at launch time or when the instance was last started.
                            </div>
                            <div>The N indicates the index of the Amazon EBS volume (such as ebs1 or ebs2).
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">/dev/xvdb</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_block_device_mapping_ephemeralN</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The virtual devices associated with ephemeral devices, if any are present. The N indicates the index of the ephemeral volume.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">/dev/xvdc</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_block_device_mapping_root</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The virtual devices or partitions associated with the root devices, or partitions on the virtual device, where the root (/ or C) file system is associated with the given instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">/dev/sda1</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_block_device_mapping_swap</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The virtual devices associated with swap. Not always present.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">/dev/sda2</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_fws_instance_monitoring</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Value showing whether the customer has enabled detailed one-minute monitoring in CloudWatch.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">enabled</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_hostname</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The private IPv4 DNS hostname of the instance.
                            </div>
                            <div>In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ip-10-0-0-1.ec2.internal</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_info</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>If there is an IAM role associated with the instance, contains information about the last time the instance profile was updated, including the instance&#x27;s LastUpdated date, InstanceProfileArn, and InstanceProfileId. Otherwise, not present.
                            </div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1" colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>InstanceProfileArn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ARN of the InstanceProfile associated with the Instance.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1" colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>InstanceProfileId</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Id of the InstanceProfile associated with the Instance.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1" colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>LastUpdated</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The last time which InstanceProfile is associated with the Instance changed.
                            </div>
                    <br/>
                </td>
            </tr>

            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_info_instanceprofilearn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IAM instance profile ARN.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">arn:aws:iam::&lt;account id&gt;:instance-profile/&lt;role name&gt;</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_info_instanceprofileid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM instance profile ID.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_info_lastupdated</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM info last updated time.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2017-05-12T02:42:27Z</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_instance_profile_role</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM instance role.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">role_name</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name></b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>If there is an IAM role associated with the instance, role-name is the name of the role, and role-name contains the temporary security credentials associated with the role. Otherwise, not present.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_accesskeyid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM role access key ID.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_code</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM code.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">Success</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_expiration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM role credentials expiration time.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2017-05-12T09:11:41Z</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_lastupdated</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM role last updated time.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2017-05-12T02:40:44Z</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_secretaccesskey</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM role secret access key.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_token</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM role token.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_iam_security_credentials_<role name>_type</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>IAM role type.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">AWS-HMAC</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_action</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Notifies the instance that it should reboot in preparation for bundling.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">none</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of this instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">i-XXXXXXXXXXXXXXXXX</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>JSON containing instance attributes, such as instance-id, private IP address, etc.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_accountid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">012345678901</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_architecture</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Instance system architecture.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">x86_64</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_availabilityzone</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Availability Zone in which the instance launched.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">us-east-1a</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_billingproducts</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Billing products for this instance.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_devpayproductcodes</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Product codes for the launched AMI.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_imageid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The AMI ID used to launch the instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ami-01234567</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_instanceid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of this instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">i-0123456789abcdef0</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_instancetype</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The type of instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">m4.large</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_kernelid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the kernel launched with this instance, if applicable.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_pendingtime</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The instance pending time.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2017-05-11T20:51:20Z</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_privateip</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The private IPv4 address of the instance.
                            </div>
                            <div>In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">10.0.0.1</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_ramdiskid</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the RAM disk specified at launch time, if applicable.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_region</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Region in which the instance launched.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">us-east-1</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_document_version</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Identity document version.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2010-08-31</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_pkcs7</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Used to verify the document&#x27;s authenticity and content against the signature.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_rsa2048</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Used to verify the document&#x27;s authenticity and content against the signature.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_identity_signature</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Data that can be used by other parties to verify its origin and authenticity.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_life_cycle</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The purchasing option of the instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">on-demand</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_instance_type</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The type of the instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">m4.large</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_local_hostname</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The private IPv4 DNS hostname of the instance.
                            </div>
                            <div>In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ip-10-0-0-1.ec2.internal</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_local_ipv4</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The private IPv4 address of the instance.
                            </div>
                            <div>In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">10.0.0.1</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_mac</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The instance&#x27;s media access control (MAC) address.
                            </div>
                            <div>In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">00:11:22:33:44:55</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_metrics_vhostmd</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Metrics; no longer available.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_device_number</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The unique device number associated with that interface. The device number corresponds to the device name; for example, a device-number of 2 is for the eth2 device.
                            </div>
                            <div>This category corresponds to the DeviceIndex and device-index fields that are used by the Amazon EC2 API and the EC2 commands for the AWS CLI.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">0</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_interface_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The elastic network interface ID.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">eni-12345678</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_ipv4_associations_<ip address></b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The private IPv4 addresses that are associated with each public-ip address and assigned to that interface.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_ipv6s</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IPv6 addresses associated with the interface. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_local_hostname</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The interface&#x27;s local hostname.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_local_ipv4s</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The private IPv4 addresses associated with the interface.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_mac</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The instance&#x27;s MAC address.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">00:11:22:33:44:55</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_owner_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the owner of the network interface.
                            </div>
                            <div>In multiple-interface environments, an interface can be attached by a third party, such as Elastic Load Balancing.
                            </div>
                            <div>Traffic on an interface is always billed to the interface owner.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">01234567890</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_public_hostname</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The interface&#x27;s public DNS (IPv4). If the instance is in a VPC, this category is only returned if the enableDnsHostnames attribute is set to true.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ec2-1-2-3-4.compute-1.amazonaws.com</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_public_ipv4s</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Elastic IP addresses associated with the interface. There may be multiple IPv4 addresses on an instance.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">1.2.3.4</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_security_group_ids</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IDs of the security groups to which the network interface belongs. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">sg-01234567,sg-01234568</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_security_groups</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Security groups to which the network interface belongs. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">secgroup1,secgroup2</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_subnet_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the subnet in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">subnet-01234567</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_subnet_ipv4_cidr_block</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IPv4 CIDR block of the subnet in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">10.0.1.0/24</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_subnet_ipv6_cidr_blocks</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IPv6 CIDR block of the subnet in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_vpc_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the VPC in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">vpc-0123456</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_vpc_ipv4_cidr_block</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IPv4 CIDR block of the VPC in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">10.0.0.0/16</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_vpc_ipv4_cidr_blocks</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IPv4 CIDR block of the VPC in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">10.0.0.0/16</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_network_interfaces_macs_<mac address>_vpc_ipv6_cidr_blocks</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The IPv6 CIDR block of the VPC in which the interface resides. Returned only for instances launched into a VPC.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_placement_availability_zone</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Availability Zone in which the instance launched.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">us-east-1a</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_placement_region</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Region in which the instance launched.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">us-east-1</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_product_codes</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Product codes associated with the instance, if any.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">aw0evgkw8e5c1q413zgy5pjce</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_profile</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>EC2 instance hardware profile.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">default-hvm</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_public_hostname</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The instance&#x27;s public DNS. If the instance is in a VPC, this category is only returned if the enableDnsHostnames attribute is set to true.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ec2-1-2-3-4.compute-1.amazonaws.com</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_public_ipv4</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The public IPv4 address. If an Elastic IP address is associated with the instance, the value returned is the Elastic IP address.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">1.2.3.4</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_public_key</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Public key. Only available if supplied at instance launch time.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_ramdisk_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the RAM disk specified at launch time, if applicable.
                            </div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_reservation_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ID of the reservation.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">r-0123456789abcdef0</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_security_groups</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The names of the security groups applied to the instance. After launch, you can only change the security groups of instances running in a VPC.
                            </div>
                            <div>Such changes are reflected here and in network/interfaces/macs/mac/security-groups.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">securitygroup1,securitygroup2</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_services_domain</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The domain for AWS resources for the region; for example, amazonaws.com for us-east-1.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">amazonaws.com</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_services_partition</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The partition that the resource is in. For standard AWS regions, the partition is aws.
                            </div>
                            <div>If you have resources in other partitions, the partition is aws-partitionname.
                            </div>
                            <div>For example, the partition for resources in the China (Beijing) region is aws-cn.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">aws</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_spot_termination_time</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The approximate time, in UTC, that the operating system for your Spot instance will receive the shutdown signal.
                            </div>
                            <div>This item is present and contains a time value only if the Spot instance has been marked for termination by Amazon EC2.
                            </div>
                            <div>The termination-time item is not set to a time if you terminated the Spot instance yourself.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2015-01-05T18:02:00Z</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>ansible_ec2_user_data</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this fact"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The instance user data.
                            </div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">#!/bin/bash</div>
                </td>
            </tr>
    </table>
    <br/><br/>



Status
------


Authors
~~~~~~~

- Silviu Dicu (@silviud)
- Vinay Dandekar (@roadmapper)
