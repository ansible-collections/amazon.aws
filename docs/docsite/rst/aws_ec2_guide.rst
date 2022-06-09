
.. _ansible_collections.amazon.aws.docsite.aws_host_inventory:

Host Inventory
``````````````

Once your nodes are spun up, you'll probably want to talk to them again.  With a cloud setup, it's best to not maintain a static list of cloud hostnames
in text files.  Rather, the best way to handle this is to use the aws_ec2 inventory plugin. See :ref:`dynamic_inventory`.

The plugin will also return instances that were created outside of Ansible and allow Ansible to manage them.

Minimal example using environment vars or instance role credentials
`````````````````````````````
Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address::
    
    plugin: aws_ec2
    regions:
      - us-east-1

- hostnames - this parameter has different settings to choose how we will like the hostname to be displayed

    hostname:
     - ip-address - this option is going to allow me to display the public ip addresses

- To use tags as hostnames use the syntax tag:Name=Value to use the hostname Name_Value, or tag:Name to use the value of the Name tag.
- If value provided does not exist in the above options, it will be used as a literal string.
     
Creating groups

keyed_groups  or groups

keyed_groups - comes in a prefix and a key format. The prefix is gonna be the name of the hostgroup that's gonna be concatenated with the key

    keyed_groups:
     - prefix: arch
       key: architecture - this is gonna create hostgroups based on architecture

For example, availability zone:
   keyed_groups:
     - prefix: az
       key: placement.availability_zone
 
 In general people prefer create groups base on tags. We can do that, using groups. Supposing to have two instances. One with these tags
  KEY          VALUE
  arch         amd_x86_64
  OS           redhat
  Name         ec2_redhat_dev
  and another one
  
  KEY          VALUE
  arch         amd_x86_64
  OS           ubuntu
  Name         ec2_ubutu_dev
  
I can create two grops redhat and ubuntu. If you specify like this is Jinja2 syntax format so quotations "" and the the string that I want to find in the value 'redhat', e.g., "'redhat' in tags.OS". Same for ubuntu

    groups:
      redhat: "'redhat' in tags.OS"
      ubuntu: "'ubuntu' in tags.OS"
    
 
 
 include_filters -  I'm gonna include in the inventory everything that's tagged
 
   include_filters:
      - tag:Project:
          - 'planets'
      - tag:Environment:
          - 'demo'
 exclude_filters:
 
 
 compose 
 https://fedorapeople.org/~toshio/ansible/latest/plugins/inventory.html
 # Set individual variables with compose
compose:
  # Use the private IP address to connect to the host
  # (note: this does not modify inventory_hostname, which is set via I(hostnames))
  ansible_host: private_ip_address
 
 You can create dynamic groups using host variables with the constructed keyed_groups option. The option groups can also be used to create groups and compose creates and modifies host variables. Here is an aws_ec2 example utilizing constructed features:
 
 If a host does not have the variables in the configuration above (i.e. tags.Name, tags, private_ip_address), the host will not be added to groups other than those that the inventory plugin creates and the ansible_host host variable will not be modified.


  
 
 Running a playbook against the inventory
 
 I wanna to be able to connect to thsoe two groups now, 
 
 
 
    
.. _ansible_collections.amazon.aws.docsite.aws_tags_and_groups:

Tags And Groups And Variables
`````````````````````````````

When using the inventory plugin, you can configure extra inventory structure based on the metadata returned by AWS.

For instance, you might use ``keyed_groups`` to create groups from instance tags::

    plugin: aws_ec2
    keyed_groups:
      - prefix: tag
        key: tags


You can then target all instances with a "class" tag where the value is "webserver" in a play::

   - hosts: tag_class_webserver
     tasks:
       - ping

You can also use these groups with 'group_vars' to set variables that are automatically applied to matching instances.  See :ref:`splitting_out_vars`.

