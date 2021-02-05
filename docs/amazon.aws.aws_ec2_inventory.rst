.. _amazon.aws.aws_ec2_inventory:


******************
amazon.aws.aws_ec2
******************

**EC2 inventory source**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Get inventory hosts from Amazon Web Services EC2.
- Uses a YAML configuration file that ends with ``aws_ec2.(yml|yaml``).



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this inventory.

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
                    <b>cache</b>
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
                            <div> ini entries:
                                    <p>[inventory]<br>cache = no</p>
                            </div>
                                <div>env:ANSIBLE_INVENTORY_CACHE</div>
                    </td>
                <td>
                        <div>Toggle to enable/disable the caching of the inventory&#x27;s source data, requires a cache plugin setup to work.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cache_connection</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                            <div> ini entries:
                                    <p>[defaults]<br>fact_caching_connection = VALUE</p>
                                    <p>[inventory]<br>cache_connection = VALUE</p>
                            </div>
                                <div>env:ANSIBLE_CACHE_PLUGIN_CONNECTION</div>
                                <div>env:ANSIBLE_INVENTORY_CACHE_CONNECTION</div>
                    </td>
                <td>
                        <div>Cache connection data or path, read cache plugin documentation for specifics.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cache_plugin</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"memory"</div>
                </td>
                    <td>
                            <div> ini entries:
                                    <p>[defaults]<br>fact_caching = memory</p>
                                    <p>[inventory]<br>cache_plugin = memory</p>
                            </div>
                                <div>env:ANSIBLE_CACHE_PLUGIN</div>
                                <div>env:ANSIBLE_INVENTORY_CACHE_PLUGIN</div>
                    </td>
                <td>
                        <div>Cache plugin to use for the inventory&#x27;s source data.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cache_prefix</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"ansible_inventory_"</div>
                </td>
                    <td>
                            <div> ini entries:
                                    <p>[default]<br>fact_caching_prefix = ansible_inventory_</p>
                                    <p>[inventory]<br>cache_prefix = ansible_inventory_</p>
                            </div>
                                <div>env:ANSIBLE_CACHE_PLUGIN_PREFIX</div>
                                <div>env:ANSIBLE_INVENTORY_CACHE_PLUGIN_PREFIX</div>
                    </td>
                <td>
                        <div>Prefix to use for cache plugin files/tables</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cache_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">3600</div>
                </td>
                    <td>
                            <div> ini entries:
                                    <p>[defaults]<br>fact_caching_timeout = 3600</p>
                                    <p>[inventory]<br>cache_timeout = 3600</p>
                            </div>
                                <div>env:ANSIBLE_CACHE_PLUGIN_TIMEOUT</div>
                                <div>env:ANSIBLE_INVENTORY_CACHE_TIMEOUT</div>
                    </td>
                <td>
                        <div>Cache duration in seconds</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>compose</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Create vars from jinja2 expressions.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>filters</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A dictionary of filter value pairs.</div>
                        <div>Available filters are listed here <a href='http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options'>http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options</a>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>groups</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Add hosts to group based on Jinja2 conditionals.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hostnames</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A list in order of precedence for hostname variables.</div>
                        <div>You can use the options specified in <a href='http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options'>http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options</a>.</div>
                        <div>To use tags as hostnames use the syntax tag:Name=Value to use the hostname Name_Value, or tag:Name to use the value of the Name tag.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>iam_role_arn</b>
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
                        <div>The ARN of the IAM role to assume to perform the inventory lookup. You should still provide AWS credentials with enough privilege to perform the AssumeRole action.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>include_extra_api_calls</b>
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
                    </td>
                <td>
                        <div>Add two additional API calls for every instance to include &#x27;persistent&#x27; and &#x27;events&#x27; host variables.</div>
                        <div>Spot instances may be persistent and instances may have associated events.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>keyed_groups</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Add hosts to group based on the values of a variable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>leading_separator</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.11</div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"yes"</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Use in conjunction with keyed_groups.</div>
                        <div>By default, a keyed group that does not have a prefix or a separator provided will have a name that starts with an underscore.</div>
                        <div>This is because the default prefix is &quot;&quot; and the default separator is &quot;_&quot;.</div>
                        <div>Set this option to False to omit the leading underscore (or other separator) if no prefix is given.</div>
                        <div>If the group name is derived from a mapping the separator is still used to concatenate the items.</div>
                        <div>To not use a separator in the group name at all, set the separator for the keyed group to an empty string instead.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>plugin</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>aws_ec2</li>
                                    <li>amazon.aws.aws_ec2</li>
                        </ul>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Token that ensures this is a source file for the plugin.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>regions</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A list of regions in which to describe EC2 instances.</div>
                        <div>If empty (the default) default this will include all regions, except possibly restricted ones like us-gov-west-1 and cn-north-1.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>strict</b>
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
                    </td>
                <td>
                        <div>If <code>yes</code> make invalid entries a fatal error, otherwise skip and continue.</div>
                        <div>Since it is possible to use facts in the expressions they might not always be available and we ignore those errors by default.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>strict_permissions</b>
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
                    </td>
                <td>
                        <div>By default if a 403 (Forbidden) error code is encountered this plugin will fail.</div>
                        <div>You can set this option to False in the inventory config file which will allow 403 errors to be gracefully skipped.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>use_contrib_script_compatible_sanitization</b>
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
                    </td>
                <td>
                        <div>By default this plugin is using a general group name sanitization to create safe and usable group names for use in Ansible. This option allows you to override that, in efforts to allow migration from the old inventory script and matches the sanitization of groups when the script&#x27;s ``replace_dash_in_groups`` option is set to ``False``. To replicate behavior of ``replace_dash_in_groups = True`` with constructed groups, you will need to replace hyphens with underscores via the regex_replace filter for those entries.</div>
                        <div>For this to work you should also turn off the TRANSFORM_INVALID_GROUP_CHARS setting, otherwise the core engine will just use the standard sanitization on top.</div>
                        <div>This is not the default as such names break certain functionality as not all characters are valid Python identifiers which group names end up being used as.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>use_extra_vars</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.11</div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                    <td>
                            <div> ini entries:
                                    <p>[inventory_plugins]<br>use_extra_vars = no</p>
                            </div>
                                <div>env:ANSIBLE_INVENTORY_USE_EXTRA_VARS</div>
                    </td>
                <td>
                        <div>Merge extra vars into the available variables for composition (highest precedence).</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - If no credentials are provided and the control node has an associated IAM instance profile then the role will be used for authentication.



Examples
--------

.. code-block:: yaml

    # Minimal example using environment vars or instance role credentials
    # Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address
    plugin: aws_ec2
    regions:
      - us-east-1

    # Example using filters, ignoring permission errors, and specifying the hostname precedence
    plugin: aws_ec2
    boto_profile: aws_profile
    # Populate inventory with instances in these regions
    regions:
      - us-east-1
      - us-east-2
    filters:
      # All instances with their `Environment` tag set to `dev`
      tag:Environment: dev
      # All dev and QA hosts
      tag:Environment:
        - dev
        - qa
      instance.group-id: sg-xxxxxxxx
    # Ignores 403 errors rather than failing
    strict_permissions: False
    # Note: I(hostnames) sets the inventory_hostname. To modify ansible_host without modifying
    # inventory_hostname use compose (see example below).
    hostnames:
      - tag:Name=Tag1,Name=Tag2  # Return specific hosts only
      - tag:CustomDNSName
      - dns-name
      - name: 'tag:Name=Tag1,Name=Tag2'
      - name: 'private-ip-address'
        separator: '_'
        prefix: 'tag:Name'

    # Example using constructed features to create groups and set ansible_host
    plugin: aws_ec2
    regions:
      - us-east-1
      - us-west-1
    # keyed_groups may be used to create custom groups
    strict: False
    keyed_groups:
      # Add e.g. x86_64 hosts to an arch_x86_64 group
      - prefix: arch
        key: 'architecture'
      # Add hosts to tag_Name_Value groups for each Name/Value tag pair
      - prefix: tag
        key: tags
      # Add hosts to e.g. instance_type_z3_tiny
      - prefix: instance_type
        key: instance_type
      # Create security_groups_sg_abcd1234 group for each SG
      - key: 'security_groups|json_query("[].group_id")'
        prefix: 'security_groups'
      # Create a group for each value of the Application tag
      - key: tags.Application
        separator: ''
      # Create a group per region e.g. aws_region_us_east_2
      - key: placement.region
        prefix: aws_region
      # Create a group (or groups) based on the value of a custom tag "Role" and add them to a metagroup called "project"
      - key: tags['Role']
        prefix: foo
        parent_group: "project"
    # Set individual variables with compose
    compose:
      # Use the private IP address to connect to the host
      # (note: this does not modify inventory_hostname, which is set via I(hostnames))
      ansible_host: private_ip_address




Status
------


Authors
~~~~~~~

- Sloane Hertel (@s-hertel)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
