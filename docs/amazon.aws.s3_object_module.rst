.. _amazon.aws.s3_object_module:


********************
amazon.aws.s3_object
********************

**Manage objects in S3**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- This module allows the user to manage the objects and directories within S3 buckets. Includes support for creating and deleting objects and directories, retrieving objects as files or strings, generating download links and copying objects that are already stored in Amazon S3.
- Support for creating or deleting S3 buckets with this module has been deprecated and will be removed in release 6.0.0.
- S3 buckets can be created or deleted using the :ref:`amazon.aws.s3_bucket <amazon.aws.s3_bucket_module>` module.



Requirements
------------
The below requirements are needed on the host that executes this module.

- python >= 3.6
- boto3 >= 1.17.0
- botocore >= 1.20.0


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
                    <b>aws_access_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div><code>AWS access key</code>. If not set then the value of the <code>AWS_ACCESS_KEY_ID</code>, <code>AWS_ACCESS_KEY</code> or <code>EC2_ACCESS_KEY</code> environment variable is used.</div>
                        <div>The <em>aws_access_key</em> and <em>profile</em> options are mutually exclusive.</div>
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
                        <div><code>AWS secret key</code>. If not set then the value of the <code>AWS_SECRET_ACCESS_KEY</code>, <code>AWS_SECRET_KEY</code>, or <code>EC2_SECRET_KEY</code> environment variable is used.</div>
                        <div>The <em>aws_secret_key</em> and <em>profile</em> options are mutually exclusive.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: ec2_secret_key, secret_key</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bucket</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Bucket name.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>content</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.3.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The content to <code>put</code> into an object.</div>
                        <div>The parameter value will be treated as a string and converted to UTF-8 before sending it to S3.</div>
                        <div>To send binary data, use the <em>content_base64</em> parameter instead.</div>
                        <div>One of <em>content</em>, <em>content_base64</em> or <em>src</em> must be specified when <em>mode=put</em> otherwise ignored.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>content_base64</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.3.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The base64-encoded binary data to <code>put</code> into an object.</div>
                        <div>Use this if you need to put raw binary data, and don&#x27;t forget to encode in base64.</div>
                        <div>One of <em>content</em>, <em>content_base64</em> or <em>src</em> must be specified when <em>mode=put</em> otherwise ignored.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>copy_src</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The source details of the object to copy.</div>
                        <div>Required if <em>mode=copy</em>.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bucket</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The name of the source bucket.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>object</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>key name of the source object.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>version_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>version ID of the source object.</div>
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
                    <b>dest</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The destination file path when downloading an object/key when <em>mode=get</em>.</div>
                        <div>Ignored when <em>mode</em> is not <code>get</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dualstack</b>
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
                        <div>Enables Amazon S3 Dual-Stack Endpoints, allowing S3 communications using both IPv4 and IPv6.</div>
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
                        <div>URL to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints). Ignored for modules where region is required. Must be specified for all other modules if region is not used. If not set then the value of the EC2_URL environment variable, if any, is used.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_endpoint_url, endpoint_url</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>encrypt</b>
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
                        <div>Asks for server-side encryption of the objects when <em>mode=put</em> or <em>mode=copy</em>.</div>
                        <div>Ignored when <em>mode</em> is neither <code>put</code> nor <code>copy</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>encryption_kms_key_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>KMS key id to use when encrypting objects using <em>encrypting=aws:kms</em>.</div>
                        <div>Ignored if <em>encryption</em> is not <code>aws:kms</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>encryption_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>AES256</b>&nbsp;&larr;</div></li>
                                    <li>aws:kms</li>
                        </ul>
                </td>
                <td>
                        <div>The encryption mode to use if <em>encrypt=true</em>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>expiry</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">600</div>
                </td>
                <td>
                        <div>Time limit (in seconds) for the URL generated and returned by S3/Walrus when performing a <em>mode=put</em> or <em>mode=geturl</em> operation.</div>
                        <div>Ignored when <em>mode</em> is neither <code>put</code> nor <code>geturl</code>.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: expiration</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>headers</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Custom headers to use when <em>mode=put</em> as a dictionary of key value pairs.</div>
                        <div>Ignored when <em>mode</em> is not <code>put</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ignore_nonexistent_bucket</b>
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
                        <div>Overrides initial bucket lookups in case bucket or IAM policies are restrictive.</div>
                        <div>This can be useful when a user may have the <code>GetObject</code> permission but no other permissions.  In which case using <em>mode=get</em> will fail unless <em>ignore_nonexistent_bucket=true</em> is specified.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>marker</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Specifies the key to start with when using list mode. Object keys are returned in alphabetical order, starting with key after the marker in order.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>max_keys</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">1000</div>
                </td>
                <td>
                        <div>Max number of results to return when <em>mode=list</em>, set this if you want to retrieve fewer than the default 1000 keys.</div>
                        <div>Ignored when <em>mode</em> is not <code>list</code>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>metadata</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Metadata to use when <em>mode=put</em> or <em>mode=copy</em> as a dictionary of key value pairs.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>get</li>
                                    <li>put</li>
                                    <li>delete</li>
                                    <li>create</li>
                                    <li>geturl</li>
                                    <li>getstr</li>
                                    <li>delobj</li>
                                    <li>list</li>
                                    <li>copy</li>
                        </ul>
                </td>
                <td>
                        <div>Switches the module behaviour between</div>
                        <div><code>put</code>: upload</div>
                        <div><code>get</code>: download</div>
                        <div><code>geturl</code>: return download URL</div>
                        <div><code>getstr</code>: download object as string</div>
                        <div><code>list</code>: list keys</div>
                        <div><code>create</code>: create bucket directories</div>
                        <div><code>delete</code>: delete bucket directories</div>
                        <div><code>delobj</code>: delete object</div>
                        <div><code>copy</code>: copy object that is already stored in another bucket</div>
                        <div>Support for creating and deleting buckets has been deprecated and will be removed in release 6.0.0.  To create and manage the bucket itself please use the <span class='module'>amazon.aws.s3_bucket</span> module.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>object</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Keyname of the object inside the bucket.</div>
                        <div>Can be used to create &quot;virtual directories&quot;, see examples.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>overwrite</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"different"</div>
                </td>
                <td>
                        <div>Force overwrite either locally on the filesystem or remotely with the object/key.</div>
                        <div>Used when <em>mode=put</em> or <em>mode=get</em>.</div>
                        <div>Ignored when when <em>mode</em> is neither <code>put</code> nor <code>get</code>.</div>
                        <div>Must be a Boolean, <code>always</code>, <code>never</code>, <code>different</code> or <code>latest</code>.</div>
                        <div><code>true</code> is the same as <code>always</code>.</div>
                        <div><code>false</code> is equal to <code>never</code>.</div>
                        <div>When this is set to <code>different</code> the MD5 sum of the local file is compared with the &#x27;ETag&#x27; of the object/key in S3.  The ETag may or may not be an MD5 digest of the object data. See the ETag response header here <a href='https://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonResponseHeaders.html'>https://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonResponseHeaders.html</a>.</div>
                        <div>When <em>mode=get</em> and <em>overwrite=latest</em> the last modified timestamp of local file is compared with the &#x27;LastModified&#x27; of the object/key in S3.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: force</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>permission</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">["private"]</div>
                </td>
                <td>
                        <div>This option lets the user set the canned permissions on the object/bucket that are created. The permissions that can be set are <code>private</code>, <code>public-read</code>, <code>public-read-write</code>, <code>authenticated-read</code> for a bucket or <code>private</code>, <code>public-read</code>, <code>public-read-write</code>, <code>aws-exec-read</code>, <code>authenticated-read</code>, <code>bucket-owner-read</code>, <code>bucket-owner-full-control</code> for an object. Multiple permissions can be specified as a list; although only the first one will be used during the initial upload of the file.</div>
                        <div>For a full list of permissions see the AWS documentation <a href='https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl'>https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl</a>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>prefix</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Limits the response to keys that begin with the specified prefix for list mode.</div>
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
                        <div>The <em>profile</em> option is mutually exclusive with the <em>aws_access_key</em>, <em>aws_secret_key</em> and <em>security_token</em> options.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_profile</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>purge_tags</b>
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
                        <div>If <em>purge_tags=true</em> and <em>tags</em> is set, existing tags will be purged from the resource to match exactly what is defined by <em>tags</em> parameter.</div>
                        <div>If the <em>tags</em> parameter is not set then tags will not be modified, even if <em>purge_tags=True</em>.</div>
                        <div>Tag keys beginning with <code>aws:</code> are reserved by Amazon and can not be modified.  As such they will be ignored for the purposes of the <em>purge_tags</em> parameter.  See the Amazon documentation for more information <a href='https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions'>https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions</a>.</div>
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
                    <b>retries</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">0</div>
                </td>
                <td>
                        <div>On recoverable failure, how many times to retry before actually failing.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: retry</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rgw</b>
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
                        <div>Enable Ceph RGW S3 support. This option requires an explicit url via <em>s3_url</em>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>s3_url</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>S3 URL endpoint for usage with Ceph, Eucalyptus and fakes3 etc. Otherwise assumes AWS.</div>
                        <div>The S3_URL alias for this option has been deprecated and will be removed in release 5.0.0.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: S3_URL</div>
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
                        <div><code>AWS STS security token</code>. If not set then the value of the <code>AWS_SECURITY_TOKEN</code> or <code>EC2_SECURITY_TOKEN</code> environment variable is used.</div>
                        <div>The <em>security_token</em> and <em>profile</em> options are mutually exclusive.</div>
                        <div>Aliases <em>aws_session_token</em> and <em>session_token</em> have been added in version 3.2.0.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_session_token, session_token, aws_security_token, access_token</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The source file path when performing a <code>put</code> operation.</div>
                        <div>One of <em>content</em>, <em>content_base64</em> or <em>src</em> must be specified when <em>mode=put</em> otherwise ignored.</div>
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
                        <div>A dictionary representing the tags to be applied to the resource.</div>
                        <div>If the <em>tags</em> parameter is not set then tags will not be modified.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: resource_tags</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>validate_bucket_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 3.1.0</div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Whether the bucket name should be validated to conform to AWS S3 naming rules.</div>
                        <div>On by default, this may be disabled for S3 backends that do not enforce these rules.</div>
                        <div>See the Amazon documentation for more information about bucket naming rules <a href='https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html'>https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html</a>.</div>
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
                        <div>When set to &quot;no&quot;, SSL certificates will not be validated for communication with the AWS APIs.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Version ID of the object inside the bucket. Can be used to get a specific version of a file if versioning is enabled in the target bucket.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - Support for *tags* and *purge_tags* was added in release 2.0.0.
   - If parameters are not set within the module, the following environment variables can be used in decreasing order of precedence ``AWS_URL`` or ``EC2_URL``, ``AWS_PROFILE`` or ``AWS_DEFAULT_PROFILE``, ``AWS_ACCESS_KEY_ID`` or ``AWS_ACCESS_KEY`` or ``EC2_ACCESS_KEY``, ``AWS_SECRET_ACCESS_KEY`` or ``AWS_SECRET_KEY`` or ``EC2_SECRET_KEY``, ``AWS_SECURITY_TOKEN`` or ``EC2_SECURITY_TOKEN``, ``AWS_REGION`` or ``EC2_REGION``, ``AWS_CA_BUNDLE``
   - When no credentials are explicitly provided the AWS SDK (boto3) that Ansible uses will fall back to its configuration files (typically ``~/.aws/credentials``). See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html for more information.
   - ``AWS_REGION`` or ``EC2_REGION`` can be typically be used to specify the AWS region, when required, but this can also be defined in the configuration files.



Examples
--------

.. code-block:: yaml

    - name: Simple PUT operation
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        src: /usr/local/myfile.txt
        mode: put

    - name: PUT operation from a rendered template
      amazon.aws.s3_object:
        bucket: mybucket
        object: /object.yaml
        content: "{{ lookup('template', 'templates/object.yaml.j2') }}"
        mode: put

    - name: Simple PUT operation in Ceph RGW S3
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        src: /usr/local/myfile.txt
        mode: put
        rgw: true
        s3_url: "http://localhost:8000"

    - name: Simple GET operation
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        dest: /usr/local/myfile.txt
        mode: get

    - name: Get a specific version of an object.
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        version: 48c9ee5131af7a716edc22df9772aa6f
        dest: /usr/local/myfile.txt
        mode: get

    - name: PUT/upload with metadata
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        src: /usr/local/myfile.txt
        mode: put
        metadata: 'Content-Encoding=gzip,Cache-Control=no-cache'

    - name: PUT/upload with custom headers
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        src: /usr/local/myfile.txt
        mode: put
        headers: 'x-amz-grant-full-control=emailAddress=owner@example.com'

    - name: List keys simple
      amazon.aws.s3_object:
        bucket: mybucket
        mode: list

    - name: List keys all options
      amazon.aws.s3_object:
        bucket: mybucket
        mode: list
        prefix: /my/desired/
        marker: /my/desired/0023.txt
        max_keys: 472

    - name: Create an empty bucket
      amazon.aws.s3_object:
        bucket: mybucket
        mode: create
        permission: public-read

    - name: Create a bucket with key as directory, in the EU region
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/directory/path
        mode: create
        region: eu-west-1

    - name: Delete a bucket and all contents
      amazon.aws.s3_object:
        bucket: mybucket
        mode: delete

    - name: GET an object but don't download if the file checksums match. New in 2.0
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        dest: /usr/local/myfile.txt
        mode: get
        overwrite: different

    - name: Delete an object from a bucket
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        mode: delobj

    - name: Copy an object already stored in another bucket
      amazon.aws.s3_object:
        bucket: mybucket
        object: /my/desired/key.txt
        mode: copy
        copy_src:
            bucket: srcbucket
            object: /source/key.txt



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
                    <b>contents</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>(for getstr operation)</td>
                <td>
                            <div>Contents of the object as string.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">Hello, world!</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>expiry</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>(for geturl operation)</td>
                <td>
                            <div>Number of seconds the presigned url is valid for.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">600</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>msg</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Message indicating the status of the operation.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">PUT operation complete</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>s3_keys</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>(for list operation)</td>
                <td>
                            <div>List of object keys.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[&#x27;prefix1/&#x27;, &#x27;prefix1/key1&#x27;, &#x27;prefix1/key2&#x27;]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>url</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>(for put and geturl operations)</td>
                <td>
                            <div>URL of the object.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">https://my-bucket.s3.amazonaws.com/my-key.txt?AWSAccessKeyId=&lt;access-key&gt;&amp;Expires=1506888865&amp;Signature=&lt;signature&gt;</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Lester Wade (@lwade)
- Sloane Hertel (@s-hertel)
- Alina Buzachis (@alinabuzachis)
