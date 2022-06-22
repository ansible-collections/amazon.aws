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
- If looking up an explicitly listed parameter by name which does not exist then the lookup will generate an error. You can use the ```default``` filter to give a default value in this case but must set the ```on_missing``` parameter to ```skip``` or ```warn```. You must also set the second parameter of the ```default``` filter to ```true``` (see examples below).
- When looking up a path for parameters under it a dictionary will be returned for each path. If there is no parameter under that path then the lookup will generate an error.
- If the lookup fails due to lack of permissions or due to an AWS client error then the aws_ssm will generate an error. If you want to continue in this case then you will have to set up two ansible tasks, one which sets a variable and ignores failures and one which uses the value of that variable with a default.  See the examples below.



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
                    <b>endpoint</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 3.3.0</div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Use a custom endpoint when connecting to SSM service.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>on_denied</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>error</b>&nbsp;&larr;</div></li>
                                    <li>skip</li>
                                    <li>warn</li>
                        </ul>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Action to take if access to the SSM parameter is denied.</div>
                        <div><code>error</code> will raise a fatal error when access to the SSM parameter is denied.</div>
                        <div><code>skip</code> will silently ignore the denied SSM parameter.</div>
                        <div><code>warn</code> will skip over the denied SSM parameter but issue a warning.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>on_missing</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>error</b>&nbsp;&larr;</div></li>
                                    <li>skip</li>
                                    <li>warn</li>
                        </ul>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Action to take if the SSM parameter is missing.</div>
                        <div><code>error</code> will raise a fatal error when the SSM parameter is missing.</div>
                        <div><code>skip</code> will silently ignore the missing SSM parameter.</div>
                        <div><code>warn</code> will skip over the missing SSM parameter but issue a warning.</div>
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

    - name: lookup ssm parameter store in specified region
      debug: msg="{{ lookup('aws_ssm', 'Hello', region='us-east-2' ) }}"

    - name: lookup ssm parameter store without decryption
      debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=False ) }}"

    - name: lookup ssm parameter store using a specified aws profile
      debug: msg="{{ lookup('aws_ssm', 'Hello', aws_profile='myprofile' ) }}"

    - name: lookup ssm parameter store using explicit aws credentials
      debug: msg="{{ lookup('aws_ssm', 'Hello', aws_access_key=my_aws_access_key, aws_secret_key=my_aws_secret_key, aws_security_token=my_security_token ) }}"

    - name: lookup ssm parameter store with all options
      debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=false, region='us-east-2', aws_profile='myprofile') }}"

    - name: lookup ssm parameter and fail if missing
      debug: msg="{{ lookup('aws_ssm', 'missing-parameter') }}"

    - name: lookup a key which doesn't exist, returning a default ('root')
      debug: msg="{{ lookup('aws_ssm', 'AdminID', on_missing="skip") | default('root', true) }}"

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

    - name: lookup ssm parameter warn if access is denied
      debug: msg="{{ lookup('aws_ssm', 'missing-parameter', on_denied="warn" ) }}"




Status
------


Authors
~~~~~~~

- Bill Wang (!UNKNOWN) <ozbillwang(at)gmail.com>
- Marat Bakeev (!UNKNOWN) <hawara(at)gmail.com>
- Michael De La Rue (!UNKNOWN) <siblemitcom.mddlr@spamgourmet.com>


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
