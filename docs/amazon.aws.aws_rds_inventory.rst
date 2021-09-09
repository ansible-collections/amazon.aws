.. _amazon.aws.aws_rds_inventory:


******************
amazon.aws.aws_rds
******************

**rds instance source**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Get instances and clusters from Amazon Web Services RDS.
- Uses a YAML configuration file that ends with aws_rds.(yml|yaml).



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
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A dictionary of filter value pairs. Available filters are listed here <a href='https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-instances.html#options'>https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-instances.html#options</a>. If you filter by db-cluster-id and <em>include_clusters</em> is True it will apply to clusters as well.</div>
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
                    <b>include_clusters</b>
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
                        <div>Whether or not to query for Aurora clusters as well as instances</div>
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
                    <b>regions</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A list of regions in which to describe RDS instances and clusters. Available regions are listed here <a href='https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html'>https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html</a></div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>statuses</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">["creating", "available"]</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>A list of desired states for instances/clusters to be added to inventory. Set to [&#x27;all&#x27;] as a shorthand to find everything.</div>
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
                        <div>By default if an AccessDenied exception is encountered this plugin will fail. You can set strict_permissions to False in the inventory config file which will allow the restrictions to be gracefully skipped.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    plugin: aws_rds
    regions:
      - us-east-1
      - ca-central-1
    keyed_groups:
      - key: 'db_parameter_groups|json_query("[].db_parameter_group_name")'
        prefix: rds_parameter_group
      - key: engine
        prefix: rds
      - key: tags
      - key: region




Status
------


Authors
~~~~~~~

- Sloane Hertel (@s-hertel)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
