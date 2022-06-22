.. _amazon.aws.aws_account_attribute_lookup:


********************************
amazon.aws.aws_account_attribute
********************************

**Look up AWS account attributes.**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Describes attributes of your AWS account. You can specify one of the listed attribute choices or omit it to see all attributes.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this lookup.

- python >= 3.6
- boto3 >= 1.17.0
- botocore >= 1.20.0


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                <th>Configuration</th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>attribute</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>supported-platforms</li>
                                    <li>default-vpc</li>
                                    <li>max-instances</li>
                                    <li>vpc-max-security-groups-per-interface</li>
                                    <li>max-elastic-ips</li>
                                    <li>vpc-max-elastic-ips</li>
                                    <li>has-ec2-classic</li>
                        </ul>
                </td>
                    <td>
                    </td>
                <td>
                        <div>The attribute for which to get the value(s).</div>
                </td>
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
                                <div>env:EC2_ACCESS_KEY</div>
                                <div>env:AWS_ACCESS_KEY</div>
                                <div>env:AWS_ACCESS_KEY_ID</div>
                    </td>
                <td>
                        <div>The AWS access key to use.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_access_key_id</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_profile</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>env:AWS_DEFAULT_PROFILE</div>
                                <div>env:AWS_PROFILE</div>
                    </td>
                <td>
                        <div>The AWS profile</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: boto_profile</div>
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
                                <div>env:EC2_SECRET_KEY</div>
                                <div>env:AWS_SECRET_KEY</div>
                                <div>env:AWS_SECRET_ACCESS_KEY</div>
                    </td>
                <td>
                        <div>The AWS secret key that corresponds to the access key.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_secret_access_key</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_security_token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>env:EC2_SECURITY_TOKEN</div>
                                <div>env:AWS_SESSION_TOKEN</div>
                                <div>env:AWS_SECURITY_TOKEN</div>
                    </td>
                <td>
                        <div>The AWS security token if using temporary access and secret keys.</div>
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
                                <div>env:EC2_REGION</div>
                                <div>env:AWS_REGION</div>
                    </td>
                <td>
                        <div>The region for which to create the connection.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    vars:
      has_ec2_classic: "{{ lookup('aws_account_attribute', attribute='has-ec2-classic') }}"
      # true | false

      default_vpc_id: "{{ lookup('aws_account_attribute', attribute='default-vpc') }}"
      # vpc-xxxxxxxx | none

      account_details: "{{ lookup('aws_account_attribute', wantlist='true') }}"
      # {'default-vpc': ['vpc-xxxxxxxx'], 'max-elastic-ips': ['5'], 'max-instances': ['20'],
      #  'supported-platforms': ['VPC', 'EC2'], 'vpc-max-elastic-ips': ['5'], 'vpc-max-security-groups-per-interface': ['5']}



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this lookup:

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
                    <b>_raw</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">-</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Returns a boolean when <em>attribute</em> is check_ec2_classic. Otherwise returns the value(s) of the attribute (or all attributes if one is not specified).</div>
                    <br/>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Sloane Hertel (@s-hertel) <shertel@redhat.com>


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
