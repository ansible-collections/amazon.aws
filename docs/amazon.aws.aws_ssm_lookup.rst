.. _amazon.aws.aws_ssm_lookup:


******************
amazon.aws.aws_ssm
******************

**Get the value for a SSM parameter or all parameters under a path.**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Get the value for an Amazon Simple Systems Manager parameter or a hierarchy of parameters. The first argument you pass the lookup can either be a parameter name or a hierarchy of parameters. Hierarchies start with a forward slash and end with the parameter name. Up to 5 layers may be specified.
- If looking up an explicitly listed parameter by name which does not exist then the lookup will return a None value which will be interpreted by Jinja2 as an empty string.  You can use the ```default``` filter to give a default value in this case but must set the second parameter to true (see examples below)
- When looking up a path for parameters under it a dictionary will be returned for each path. If there is no parameter under that path then the return will be successful but the dictionary will be empty.
- If the lookup fails due to lack of permissions or due to an AWS client error then the aws_ssm will generate an error, normally crashing the current ansible task.  This is normally the right thing since ignoring a value that IAM isn't giving access to could cause bigger problems and wrong behaviour or loss of data.  If you want to continue in this case then you will have to set up two ansible tasks, one which sets a variable and ignores failures one which uses the value of that variable with a default.  See the examples below.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this lookup.

- boto3
- botocore


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
                    <b>bypath</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"no"</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A boolean to indicate whether the parameter is provided as a hierarchy.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>decrypt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"yes"</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A boolean to indicate whether to decrypt the parameter.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>recursive</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"no"</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A boolean to indicate whether to retrieve all parameters within a hierarchy.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>shortnames</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"no"</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Indicates whether to return the name only without path if using a parameter hierarchy.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # lookup sample:
    - name: lookup ssm parameter store in the current region
      debug: msg="{{ lookup('aws_ssm', 'Hello' ) }}"

    - name: lookup ssm parameter store in nominated region
      debug: msg="{{ lookup('aws_ssm', 'Hello', region='us-east-2' ) }}"

    - name: lookup ssm parameter store without decrypted
      debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=False ) }}"

    - name: lookup ssm parameter store in nominated aws profile
      debug: msg="{{ lookup('aws_ssm', 'Hello', aws_profile='myprofile' ) }}"

    - name: lookup ssm parameter store using explicit aws credentials
      debug: msg="{{ lookup('aws_ssm', 'Hello', aws_access_key=my_aws_access_key, aws_secret_key=my_aws_secret_key, aws_security_token=my_security_token ) }}"

    - name: lookup ssm parameter store with all options.
      debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=false, region='us-east-2', aws_profile='myprofile') }}"

    - name: lookup a key which doesn't exist, returns ""
      debug: msg="{{ lookup('aws_ssm', 'NoKey') }}"

    - name: lookup a key which doesn't exist, returning a default ('root')
      debug: msg="{{ lookup('aws_ssm', 'AdminID') | default('root', true) }}"

    - name: lookup a key which doesn't exist failing to store it in a fact
      set_fact:
        temp_secret: "{{ lookup('aws_ssm', '/NoAccess/hiddensecret') }}"
      ignore_errors: true

    - name: show fact default to "access failed" if we don't have access
      debug: msg="{{ 'the secret was:' ~ temp_secret | default('could not access secret') }}"

    - name: return a dictionary of ssm parameters from a hierarchy path
      debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region='ap-southeast-2', bypath=true, recursive=true ) }}"

    - name: return a dictionary of ssm parameters from a hierarchy path with shortened names (param instead of /PATH/to/param)
      debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region='ap-southeast-2', shortnames=true, bypath=true, recursive=true ) }}"

    - name: Iterate over a parameter hierarchy (one iteration per parameter)
      debug: msg='Key contains {{ item.key }} , with value {{ item.value }}'
      loop: '{{ lookup("aws_ssm", "/demo/", region="ap-southeast-2", bypath=True) | dict2items }}'

    - name: Iterate over multiple paths as dictionaries (one iteration per path)
      debug: msg='Path contains {{ item }}'
      loop: '{{ lookup("aws_ssm", "/demo/", "/demo1/", bypath=True)}}'




Status
------


Authors
~~~~~~~

- Bill Wang <ozbillwang(at)gmail.com>
- Marat Bakeev <hawara(at)gmail.com>
- Michael De La Rue <siblemitcom.mddlr@spamgourmet.com>


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
