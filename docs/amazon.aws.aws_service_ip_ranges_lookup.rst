.. _amazon.aws.aws_service_ip_ranges_lookup:


********************************
amazon.aws.aws_service_ip_ranges
********************************

**Look up the IP ranges for services provided in AWS such as EC2 and S3.**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- AWS publishes IP ranges used on the public internet by EC2, S3, CloudFront, CodeBuild, Route53, and Route53 Health Checking.
- This module produces a list of all the ranges (by default) or can narrow down the list to the specified region or service.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this lookup.

- must have public internet connectivity


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
                    <b>region</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>The AWS region to narrow the ranges to. Examples: us-east-1, eu-west-2, ap-southeast-1</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>service</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>The service to filter ranges by. Options: EC2, S3, CLOUDFRONT, CODEbUILD, ROUTE53, ROUTE53_HEALTHCHECKS</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    vars:
      ec2_ranges: "{{ lookup('aws_service_ip_ranges', region='ap-southeast-2', service='EC2', wantlist=True) }}"
    tasks:

    - name: "use list return option and iterate as a loop"
      debug: msg="{% for cidr in ec2_ranges %}{{ cidr }} {% endfor %}"
    # "52.62.0.0/15 52.64.0.0/17 52.64.128.0/17 52.65.0.0/16 52.95.241.0/24 52.95.255.16/28 54.66.0.0/16 "

    - name: "Pull S3 IP ranges, and print the default return style"
      debug: msg="{{ lookup('aws_service_ip_ranges', region='us-east-1', service='S3') }}"
    # "52.92.16.0/20,52.216.0.0/15,54.231.0.0/17"



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
                            <div>comma-separated list of CIDR ranges</div>
                    <br/>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- James Turner <turnerjsm@gmail.com>


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
