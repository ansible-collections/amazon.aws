.. _ansible_collections.amazon.aws.docsite.dynamic_inventory:


Dynamic Inventory Plugin
========================

A dynamic inventory plugin allows users to point at data sources to compile the inventory of hosts that Ansible uses to target tasks, either via the ``-i /path/to/file`` and/or ``-i 'host1, host2'`` command line parameters or from other configuration sources.

When using Ansible with AWS, inventory file maintenance will be a hectic task as AWS frequently changes IPs, autoscaling instances, and more.
Once your AWS EC2 hosts are spun up, you'll probably want to talk to them again.
With a cloud setup, it's best not to maintain a static list of cloud hostnames in text files.
Rather, the best way to handle this is to use the ``aws_ec2`` dynamic inventory plugin.

The ``aws_ec2`` dynamic inventory plugin makes API calls to AWS to get a list of inventory hosts from Amazon Web Services EC2 in the run time.
It gives the EC2 instance details dynamically to manage the AWS infrastructure.

The plugin will also return instances that were created outside of Ansible and allow Ansible to manage them.

To start using the ``aws_ec2`` dynamic inventory plugin with a YAML configuration source, create a file with the accepted filename schema documented for the plugin (a YAML configuration file that ends with ``aws_ec2.(yml|yaml)``, e.g., ``demo.aws_ec2.yml``), then add ``plugin: amazon.aws.aws_ec2``. Use the fully qualified name if the plugin is in a collection.

.. _ansible_collections.amazon.aws.docsite.using_inventory_plugin:

Authentication
==============

If your Ansible controller is not in AWS, authentication is handled by either
specifying your access and secret key as ENV variables or inventory plugin arguments. 

For environment variables:

.. code-block:: bash

    export AWS_ACCESS_KEY_ID='AK123'
    export AWS_SECRET_ACCESS_KEY='abc123'

The ``AWS_SECURITY_TOKEN`` environment variable can also be used, but is only supported for backward compatibility.
The ``AWS_SECURITY_TOKEN`` is a replacement for ``AWS_SESSION_TOKEN`` and it is only needed when you are using temporary credentials.

Or you can set ``aws_access_key``, ``aws_secret_key``, and ``security_token`` inside the inventory configuration file.

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2

    # The access key for your AWS account.
    aws_access_key: <YOUR-AWS-ACCESS-KEY-HERE>
    # The secret access key for your AWS account.
    aws_secret_key: <YOUR-AWS-SECRET-KEY-HERE>

If you use different credentials for different tools or applications, you can use profiles.

The ``profile`` argument is mutually exclusive with the ``aws_access_key``, ``aws_secret_key`` and ``security_token`` options.
When no credentials are explicitly provided then the AWS SDK (boto3) which Ansible uses will fall back to its configuration files (typically ``~/.aws/credentials``).
The shared credentials file has a default location of ``~/.aws/credentials``.
You can change the location of the shared credentials file by setting the ``AWS_SHARED_CREDENTIALS_FILE`` environment variable.

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2

    # Attach the default AWS profile
    aws_profile: default

    # You could use Jinja2 to attach the AWS profile from the environment variable.
    aws_profile: "{{ lookup('env', 'AWS_PROFILE') | default('dev-profile', true) }}"

You can also set your AWS profile as an ENV variable:

.. code-block:: bash

    export AWS_PROFILE='test-profile'


If your Ansible controller is running on an EC2 instance with an assigned IAM Role, the credential may be omitted.
See the documentation for the controller `for more details <https://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#ug-source-ec2>`_.

You can also use the ARN of the IAM role to assume to perform the inventory lookup.
This can be useful for connecting across different accounts, or to limit user access. 
To do so, you should specify the ``iam_role_arn``.
You should still provide AWS credentials with enough privilege to perform the AssumeRole action.
       
.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2

    iam_role_arn: arn:aws:iam::1234567890:role/assumed-ansible


Minimal Example
===============

Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address.

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2

    # This sets the region. If empty (the default) default this will include all regions, except possibly
    # restricted ones like us-gov-west-1 and cn-north-1.
    regions:
    - us-east-1

After providing any required options, you can view the populated inventory with ``ansible-inventory -i demo.aws_ec2.yml --graph``:

.. code-block:: text

   @all:
    |--@aws_ec2:
    |  |--ip-10-210-0-189.ec2.internal
    |  |--ip-10-210-0-195.ec2.internal
    |--@ungrouped:


Allowed Options
===============

Some of the ``aws_ec2`` dynamic inventory plugin options are explained in detail below. For a full list see `the plugin documentation <https://docs.ansible.com/ansible/latest/collections/amazon/aws/aws_ec2_inventory.html#id3>`_.

``hostnames``
-------------

``hostnames`` option provides different settings to choose how the hostname will be displayed.

Some examples are shown below:

.. code-block:: yaml

  hostnames:
    # This option allows displaying the public ip addresses.
    - ip-address
  
    # This option allows displaying the private ip addresses using `tag:Name` as a prefix.
    # `name` can be one of the options specified in http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options.
    - name: 'private-ip-address'
      separator: '_'
      prefix: 'tag:Name'
    
    # Using literal values for hostname
    # # Hostname will be aws-test_literal
    - name: 'test_literal'
      separator: '-'       
      prefix: 'aws'
  
    # To use tags as hostnames use the syntax `tag:Name=Value` to use the hostname `Name_Value`, or
    # `tag:Name` to use the value of the Name tag. If value provided does not exist in the above options,
    # it will be used as a literal string.
    - name: 'tag:Tag1=Test1,Tag2=Test2'
    
    # Use dns-name attribute as hostname
    - dns-name

    # You can also specify a list in order of precedence for hostname variables.
    - ip-address
    - dns-name
    - tag:Name
    - private-ip-address

By default, the inventory will only return the first match one of the ``hostnames`` entries.
You may want to get all the potential matches in your inventory, this also implies you will get
duplicated entries. To switch to this behavior, set the ``allow_duplicated_hosts`` configuration key to ``True``.

``keyed_groups``
----------------

You can create dynamic groups using host variables with the ``keyed_groups`` option. ``keyed_groups`` comes in a prefix and a key format.
The prefix will be the name of the host group that is to be concatenated with the key.

Some examples are shown below:

.. code-block:: yaml

    keyed_groups:
    # This creates host groups based on architecture.
    - prefix: arch
      key: architecture
    
    # This creates host groups based on `x86_64` architecture.
    - prefix: arch
      key: architecture
      value:
          'x86_64'
    
    # This creates host groups based on availability zone.
    - prefix: az
      key: placement.availability_zone
    
    # If the EC2 tag Name had the value `redhat` the tag variable would be: `tag_Name_redhat`.
    # Similarly, if a tag existed for an AWS EC2 instance as `Applications` with the value of `nodejs` the  
    # variable would be: `tag_Applications_nodejs`.
    - prefix: tag
      key: tags
    
    # This creates host groups using instance_type, e.g., `instance_type_z3_tiny`.
    - prefix: instance_type
      key: instance_type

    # This creates host groups using security_groups id, e.g., `security_groups_sg_abcd1234` group for each security group.
    - key: 'security_groups|json_query("[].group_id")'
      prefix: 'security_groups'
    
    # This creates a host group for each value of the Application tag.
    - key: tags.Application
      separator: ''

    # This creates a host group per region e.g., `aws_region_us_east_2`.
    - key: placement.region
      prefix: aws_region

    # This creates host groups based on the value of a custom tag `Role` and adds them to a metagroup called `project`.
    - key: tags['Role']
      prefix: foo
      parent_group: "project"
    
    # This creates a common parent group for all EC2 availability zones.
    - key: placement.availability_zone
      parent_group: all_ec2_zones
    
    # This creates a group per distro (distro_CentOS, distro_Debian) and assigns the hosts that have matching values to it,
    # using the default separator "_".
    - prefix: distro
      key: ansible_distribution


``groups``
----------

It is also possible to create groups using the ``groups`` option.

Some examples are shown below:

.. code-block:: yaml

  groups:
    # This created two groups - `Production` and `PreProduction` based on tags
    # These conditionals are expressed using Jinja2 syntax.
    redhat: "'Production' in tags.Environment"
    ubuntu: "'PreProduction' in tags.Environment"

    # This created a libvpc group based on specific condition on `vpc_id`.
    libvpc: vpc_id == 'vpc-####'


``compose``
-----------

``compose`` creates and modifies host variables from Jinja2 expressions.

.. code-block:: yaml

  compose:
    # This sets the ansible_host variable to connect with the private IP address without changing the hostname.
    ansible_host: private_ip_address

    # This sets location_vars variable as a dictionary with location as a key.
    location_vars:
      location: "east_coast"
      server_type: "ansible_hostname | regex_replace ('(.{6})(.{2}).*', '\\2')"
    
    # This sets location variable.
    location: "'east_coast'"

    # This lets you connect over SSM to the instance id.
    ansible_host: instance_id
    ansible_connection: 'community.aws.aws_ssm'

    # This defines combinations of host servers, IP addresses, and related SSH private keys.
    ansible_host: private_ip_address
    ansible_user: centos
    ansible_ssh_private_key_file: /path/to/private_key_file

    # This sets the ec2_security_group_ids variable.
    ec2_security_group_ids: security_groups | map(attribute='group_id') | list |  join(',')

    # Host variables that are strings need to be wrapped with two sets of quotes.
    # See https://docs.ansible.com/ansible/latest/plugins/inventory.html#using-inventory-plugins for details.
    ansible_connection: '"community.aws.aws_ssm"'
    ansible_user: '"ssm-user"'


``include_filters`` and ``exclude_filters``
-------------------------------------------

``include_filters`` and ``exclude_filters`` options give you the ability to compose the inventory with several queries (see `available filters <http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options>`_).

.. code-block:: yaml

  include_filters:
  # This includes everything in the inventory that has the following tags.
  - tag:Project:
      - 'planets'
  - tag:Environment:
      - 'demo'
  
  # This excludes everything from the inventory that has the following tag:Name.
  exclude_filters:
  - tag:Name:
      - '{{ resource_prefix }}_3'


``filters``
-----------

``filters`` are used to filter out AWS EC2 instances based on conditions (see `available filters <http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options>`_).

.. code-block:: yaml

  filters:
    # This selects only running instances with tag `Environment` tag set to `dev`.
    tag:Environment: dev
    instance-state-name : running

    # This selects only instances with tag `Environment` tag set to `dev` and `qa` and specific security group id.
    tag:Environment:
      - dev
      - qa
    instance.group-id: sg-xxxxxxxx
   
    # This selects only instances with tag `Name` fulfilling specific conditions.
    - tag:Name:
      - dev-*
      - share-resource
      - hotfix


``use_contrib_script_compatible_ec2_tag_keys`` and ``use_contrib_script_compatible_sanitization``
-------------------------------------------------------------------------------------------------

``use_contrib_script_compatible_ec2_tag_keys`` exposes the host tags with ec2_tag_TAGNAME keys like the old ec2.py inventory script when it's True.

By default the ``aws_ec2`` plugin is using a general group name sanitization to create safe and usable group names for use in Ansible.

``use_contrib_script_compatible_ec2_tag_keys`` allows you to override that, in efforts to allow migration from the old inventory script and matches the sanitization of groups when the script's replace_dash_in_groups option is set to False.
To replicate behavior of replace_dash_in_groups = True with constructed groups, you will need to replace hyphens with underscores via the regex_replace filter for those entries.

For this to work you should also turn off the TRANSFORM_INVALID_GROUP_CHARS setting, otherwise the core engine will just use the standard sanitization on top.

This is not the default as such names break certain functionality as not all characters are valid Python identifiers which group names end up being used as.

The use of this feature is discouraged and we advise to migrate to the new tags structure.

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2
    regions:
    - us-east-1
    filters:
      tag:Name:
      - 'instance-*'
    hostnames:
    - tag:Name
    use_contrib_script_compatible_sanitization: True
    use_contrib_script_compatible_ec2_tag_keys: True

After providing any required options, you can view the populated inventory with ``ansible-inventory -i demo.aws_ec2.yml --list``:

.. code-block:: text

  {
    "_meta": {
        "hostvars": {
            "instance-01": {
                "aws_ami_launch_index_ec2": 0,
                "aws_architecture_ec2": "x86_64",
                ...
                "ebs_optimized": false,
                "ec2_tag_Environment": "dev",
                "ec2_tag_Name": "instance-01",
                "ec2_tag_Tag1": "Test1",
                "ec2_tag_Tag2": "Test2",
                "ena_support": true,
                "enclave_options": {
                    "enabled": false
                },
                ...
            },
            "instance-02": {
              ...
              "ebs_optimized": false,
              "ec2_tag_Environment": "dev",
              "ec2_tag_Name": "instance-02",
              "ec2_tag_Tag1": "Test3",
              "ec2_tag_Tag2": "Test4",
              "ena_support": true,
              "enclave_options": {
                  "enabled": false
              },
              ...
            }
        }
    },
    all": {
          "children": [
              "aws_ec2",
              "ungrouped"
          ]
      },
      "aws_ec2": {
          "hosts": [
              "instance-01",
              "instance-02"
          ]
      }
  }


``hostvars_prefix`` and ``hostvars_suffix``
-------------------------------------------

``hostvars_prefix`` and ``hostvars_sufix`` allow to set up a prefix and suffix for host variables.

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2
    regions:
    - us-east-1
    filters:
      tag:Name:
      - 'instance-*'
    hostvars_prefix: 'aws_'
    hostvars_suffix: '_ec2'
    hostnames:
    - tag:Name

Now the output of ``ansible-inventory -i demo.aws_ec2.yml --list``:

.. code-block:: text

  {
    "_meta": {
        "hostvars": {
            "instance-01": {
                "aws_ami_launch_index_ec2": 0,
                "aws_architecture_ec2": "x86_64",
                "aws_block_device_mappings_ec2": [
                    {
                        "device_name": "/dev/sda1",
                        "ebs": {
                            "attach_time": "2022-06-27T09:04:57+00:00",
                            "delete_on_termination": true,
                            "status": "attached",
                            "volume_id": "vol-06e065bca44e6eae5"
                        }
                    }
                ],
                "aws_capacity_reservation_specification_ec2": {
                    "capacity_reservation_preference": "open"
                }
                ...,
            },
            "instance-02": {
              ...,
            }
        }
    },
    all": {
          "children": [
              "aws_ec2",
              "ungrouped"
          ]
      },
      "aws_ec2": {
          "hosts": [
              "instance-01",
              "instance-02"
          ]
      }
  }


``strict`` and ``strict_permissions``
-------------------------------------

``strict: False`` will skip instead of producing an error if there are missing facts.

``strict_permissions: False`` will ignore 403 errors rather than failing.


``use_ssm_inventory``
---------------------

``use_ssm_inventory: True`` will include SSM inventory variables into hostvars for ssm-configured instances.

``cache``
---------

``aws_ec2`` inventory plugin support caching can use the general settings for the fact cache defined in the ``ansible.cfg`` file's ``[defaults]`` section or define inventory-specific settings in the ``[inventory]`` section.
You can can define plugin-specific cache settings in the config file:

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: aws_ec2
    # This enables cache.
    cache: yes
    # Plugin to be used.
    cache_plugin: jsonfile
    cache_timeout: 7200
    # Location where files are stored in the cache.
    cache_connection: /tmp/aws_inventory
    cache_prefix: aws_ec2

Here is an example of setting inventory caching with some fact caching defaults for the cache plugin used and the timeout in an ``ansible.cfg`` file:

.. code-block:: ini

  [defaults]
  fact_caching = ansible.builtin.jsonfile
  fact_caching_connection = /tmp/ansible_facts
  cache_timeout = 3600

  [inventory]
  cache = yes
  cache_connection = /tmp/ansible_inventory


Complex Example
===============

Here is an ``aws_ec2`` complex example utilizing some of the previously listed options:

.. code-block:: yaml

    # demo.aws_ec2.yml
    plugin: amazon.aws.aws_ec2
    regions:
      - us-east-1
      - us-east-2
    keyed_groups:
      # add hosts to tag_Name_value groups for each aws_ec2 host's tags.Name variable.
      - key: tags.Name
        prefix: tag_Name_
        separator: ""
    groups:
      # add hosts to the group dev if any of the dictionary's keys or values is the word 'dev'.
      development: "'dev' in (tags|list)"
    filters:
      tag:Name:
        - 'instance-01'
        - 'instance-03'
    include_filters:
    - tag:Name:
      - 'instance-02'
      - 'instance-04'
    exclude_filters:
    - tag:Name:
      - 'instance-03'
      - 'instance-04'
    hostnames:
      # You can also specify a list in order of precedence for hostname variables.
      - ip-address
      - dns-name
      - tag:Name
      - private-ip-address
    compose:
      # This sets the `ansible_host` variable to connect with the private IP address without changing the hostname.
      ansible_host: private_ip_address

If a host does not have the variables in the configuration above (i.e. ``tags.Name``, ``tags``, ``private_ip_address``), the host will not be added to groups other than those that the inventory plugin creates and the ``ansible_host`` host variable will not be modified.

Now the output of ``ansible-inventory -i demo.aws_ec2.yml --graph``:

.. code-block:: text

    @all:
    |--@aws_ec2:
    |  |--instance-01
    |  |--instance-02
    |--@tag_Name_instance_01:
    |  |--instance-01
    |--@tag_Name_instance_02:
    |  |--instance-02
    |--@ungrouped:


Using Dynamic Inventory Inside Playbook
=======================================

If you want to use dynamic inventory inside the playbook, you just need to mention the group name in the hosts variable as shown below.

.. code-block:: yaml

    ---
    - name: Ansible Test Playbook
      gather_facts: false
      hosts: tag_Name_instance_02
      
      tasks:
        - name: Run Shell Command
          command: echo "Hello World"
