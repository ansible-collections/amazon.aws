# Community AWS Collection
[![Shippable build status](https://api.shippable.com/projects//5e5ed2ae0fcc0d0006d2c037badge?branch=main)](https://api.shippable.com/projects/i5e5ed2ae0fcc0d0006d2c037/badge?branch=main)
<!--[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/community.aws)](https://codecov.io/gh/ansible-collections/community.aws)-->

The Ansible Community AWS collection includes a variety of Ansible content to help automate the management of AWS instances. This collection is maintained by the Ansible community.

AWS related modules and plugins supported by the Ansible Cloud team are in the [amazon.aws](https://github.com/ansible-collections/amazon.aws) collection.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.10**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

## Python version compatibility

This collection depends on the AWS SDK for Python (Boto3 and Botocore). As AWS has [ceased supporting Python 2.6](https://aws.amazon.com/blogs/developer/deprecation-of-python-2-6-and-python-3-3-in-botocore-boto3-and-the-aws-cli/), this collection requires Python 2.7 or greater.

## Included content
<!--start collection content-->
### Connection plugins
Name | Description
--- | ---
[community.aws.aws_ssm](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_ssm_connection.rst)|execute via AWS Systems Manager

### Modules
Name | Description
--- | ---
[community.aws.aws_acm](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_acm_module.rst)|Upload and delete certificates in the AWS Certificate Manager service
[community.aws.aws_acm_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_acm_info_module.rst)|Retrieve certificate information from AWS Certificate Manager service
[community.aws.aws_api_gateway](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_api_gateway_module.rst)|Manage AWS API Gateway APIs
[community.aws.aws_application_scaling_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_application_scaling_policy_module.rst)|Manage Application Auto Scaling Scaling Policies
[community.aws.aws_batch_compute_environment](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_batch_compute_environment_module.rst)|Manage AWS Batch Compute Environments
[community.aws.aws_batch_job_definition](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_batch_job_definition_module.rst)|Manage AWS Batch Job Definitions
[community.aws.aws_batch_job_queue](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_batch_job_queue_module.rst)|Manage AWS Batch Job Queues
[community.aws.aws_codebuild](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_codebuild_module.rst)|Create or delete an AWS CodeBuild project
[community.aws.aws_codecommit](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_codecommit_module.rst)|Manage repositories in AWS CodeCommit
[community.aws.aws_codepipeline](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_codepipeline_module.rst)|Create or delete AWS CodePipelines
[community.aws.aws_config_aggregation_authorization](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_config_aggregation_authorization_module.rst)|Manage cross-account AWS Config authorizations
[community.aws.aws_config_aggregator](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_config_aggregator_module.rst)|Manage AWS Config aggregations across multiple accounts
[community.aws.aws_config_delivery_channel](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_config_delivery_channel_module.rst)|Manage AWS Config delivery channels
[community.aws.aws_config_recorder](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_config_recorder_module.rst)|Manage AWS Config Recorders
[community.aws.aws_config_rule](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_config_rule_module.rst)|Manage AWS Config resources
[community.aws.aws_direct_connect_confirm_connection](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_direct_connect_confirm_connection_module.rst)|Confirms the creation of a hosted DirectConnect connection.
[community.aws.aws_direct_connect_connection](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_direct_connect_connection_module.rst)|Creates, deletes, modifies a DirectConnect connection
[community.aws.aws_direct_connect_gateway](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_direct_connect_gateway_module.rst)|Manage AWS Direct Connect gateway
[community.aws.aws_direct_connect_link_aggregation_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_direct_connect_link_aggregation_group_module.rst)|Manage Direct Connect LAG bundles
[community.aws.aws_direct_connect_virtual_interface](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_direct_connect_virtual_interface_module.rst)|Manage Direct Connect virtual interfaces
[community.aws.aws_eks_cluster](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_eks_cluster_module.rst)|Manage Elastic Kubernetes Service Clusters
[community.aws.aws_elasticbeanstalk_app](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_elasticbeanstalk_app_module.rst)|Create, update, and delete an elastic beanstalk application
[community.aws.aws_glue_connection](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_glue_connection_module.rst)|Manage an AWS Glue connection
[community.aws.aws_glue_job](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_glue_job_module.rst)|Manage an AWS Glue job
[community.aws.aws_inspector_target](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_inspector_target_module.rst)|Create, Update and Delete Amazon Inspector Assessment Targets
[community.aws.aws_kms](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_kms_module.rst)|Perform various KMS management tasks.
[community.aws.aws_kms_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_kms_info_module.rst)|Gather information about AWS KMS keys
[community.aws.aws_region_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_region_info_module.rst)|Gather information about AWS regions.
[community.aws.aws_s3_bucket_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_s3_bucket_info_module.rst)|Lists S3 buckets in AWS
[community.aws.aws_s3_cors](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_s3_cors_module.rst)|Manage CORS for S3 buckets in AWS
[community.aws.aws_secret](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_secret_module.rst)|Manage secrets stored in AWS Secrets Manager.
[community.aws.aws_ses_identity](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_ses_identity_module.rst)|Manages SES email and domain identity
[community.aws.aws_ses_identity_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_ses_identity_policy_module.rst)|Manages SES sending authorization policies
[community.aws.aws_ses_rule_set](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_ses_rule_set_module.rst)|Manages SES inbound receipt rule sets
[community.aws.aws_sgw_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_sgw_info_module.rst)|Fetch AWS Storage Gateway information
[community.aws.aws_ssm_parameter_store](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_ssm_parameter_store_module.rst)|Manage key-value pairs in aws parameter store.
[community.aws.aws_step_functions_state_machine](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_step_functions_state_machine_module.rst)|Manage AWS Step Functions state machines
[community.aws.aws_step_functions_state_machine_execution](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_step_functions_state_machine_execution_module.rst)|Start or stop execution of an AWS Step Functions state machine.
[community.aws.aws_waf_condition](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_waf_condition_module.rst)|Create and delete WAF Conditions
[community.aws.aws_waf_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_waf_info_module.rst)|Retrieve information for WAF ACLs, Rule , Conditions and Filters.
[community.aws.aws_waf_rule](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_waf_rule_module.rst)|Create and delete WAF Rules
[community.aws.aws_waf_web_acl](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.aws_waf_web_acl_module.rst)|Create and delete WAF Web ACLs.
[community.aws.cloudformation_exports_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudformation_exports_info_module.rst)|Read a value from CloudFormation Exports
[community.aws.cloudformation_stack_set](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudformation_stack_set_module.rst)|Manage groups of CloudFormation stacks
[community.aws.cloudfront_distribution](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudfront_distribution_module.rst)|Create, update and delete AWS CloudFront distributions.
[community.aws.cloudfront_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudfront_info_module.rst)|Obtain facts about an AWS CloudFront distribution
[community.aws.cloudfront_invalidation](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudfront_invalidation_module.rst)|create invalidations for AWS CloudFront distributions
[community.aws.cloudfront_origin_access_identity](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudfront_origin_access_identity_module.rst)|Create, update and delete origin access identities for a CloudFront distribution
[community.aws.cloudtrail](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudtrail_module.rst)|manage CloudTrail create, delete, update
[community.aws.cloudwatchevent_rule](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudwatchevent_rule_module.rst)|Manage CloudWatch Event rules and targets
[community.aws.cloudwatchlogs_log_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudwatchlogs_log_group_module.rst)|create or delete log_group in CloudWatchLogs
[community.aws.cloudwatchlogs_log_group_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudwatchlogs_log_group_info_module.rst)|Get information about log_group in CloudWatchLogs
[community.aws.cloudwatchlogs_log_group_metric_filter](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.cloudwatchlogs_log_group_metric_filter_module.rst)|Manage CloudWatch log group metric filter
[community.aws.data_pipeline](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.data_pipeline_module.rst)|Create and manage AWS Datapipelines
[community.aws.dms_endpoint](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.dms_endpoint_module.rst)|Creates or destroys a data migration services endpoint
[community.aws.dms_replication_subnet_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.dms_replication_subnet_group_module.rst)|creates or destroys a data migration services subnet group
[community.aws.dynamodb_table](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.dynamodb_table_module.rst)|Create, update or delete AWS Dynamo DB tables
[community.aws.dynamodb_ttl](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.dynamodb_ttl_module.rst)|Set TTL for a given DynamoDB table
[community.aws.ec2_ami_copy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_ami_copy_module.rst)|copies AMI between AWS regions, return new image id
[community.aws.ec2_asg](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_asg_module.rst)|Create or delete AWS AutoScaling Groups (ASGs)
[community.aws.ec2_asg_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_asg_info_module.rst)|Gather information about ec2 Auto Scaling Groups (ASGs) in AWS
[community.aws.ec2_asg_lifecycle_hook](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_asg_lifecycle_hook_module.rst)|Create, delete or update AWS ASG Lifecycle Hooks.
[community.aws.ec2_customer_gateway](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_customer_gateway_module.rst)|Manage an AWS customer gateway
[community.aws.ec2_customer_gateway_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_customer_gateway_info_module.rst)|Gather information about customer gateways in AWS
[community.aws.ec2_eip](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_eip_module.rst)|manages EC2 elastic IP (EIP) addresses.
[community.aws.ec2_eip_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_eip_info_module.rst)|List EC2 EIP details
[community.aws.ec2_elb](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_elb_module.rst)|De-registers or registers instances from EC2 ELBs
[community.aws.ec2_elb_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_elb_info_module.rst)|Gather information about EC2 Elastic Load Balancers in AWS
[community.aws.ec2_instance](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_instance_module.rst)|Create & manage EC2 instances
[community.aws.ec2_instance_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_instance_info_module.rst)|Gather information about ec2 instances in AWS
[community.aws.ec2_launch_template](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_launch_template_module.rst)|Manage EC2 launch templates
[community.aws.ec2_lc](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_lc_module.rst)|Create or delete AWS Autoscaling Launch Configurations
[community.aws.ec2_lc_find](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_lc_find_module.rst)|Find AWS Autoscaling Launch Configurations
[community.aws.ec2_lc_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_lc_info_module.rst)|Gather information about AWS Autoscaling Launch Configurations.
[community.aws.ec2_metric_alarm](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_metric_alarm_module.rst)|Create/update or delete AWS Cloudwatch 'metric alarms'
[community.aws.ec2_placement_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_placement_group_module.rst)|Create or delete an EC2 Placement Group
[community.aws.ec2_placement_group_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_placement_group_info_module.rst)|List EC2 Placement Group(s) details
[community.aws.ec2_scaling_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_scaling_policy_module.rst)|Create or delete AWS scaling policies for Autoscaling groups
[community.aws.ec2_snapshot_copy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_snapshot_copy_module.rst)|Copies an EC2 snapshot and returns the new Snapshot ID.
[community.aws.ec2_transit_gateway](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_transit_gateway_module.rst)|Create and delete AWS Transit Gateways
[community.aws.ec2_transit_gateway_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_transit_gateway_info_module.rst)|Gather information about ec2 transit gateways in AWS
[community.aws.ec2_vpc_egress_igw](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_egress_igw_module.rst)|Manage an AWS VPC Egress Only Internet gateway
[community.aws.ec2_vpc_endpoint](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_endpoint_module.rst)|Create and delete AWS VPC Endpoints.
[community.aws.ec2_vpc_endpoint_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_endpoint_info_module.rst)|Retrieves AWS VPC endpoints details using AWS methods.
[community.aws.ec2_vpc_igw](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_igw_module.rst)|Manage an AWS VPC Internet gateway
[community.aws.ec2_vpc_igw_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_igw_info_module.rst)|Gather information about internet gateways in AWS
[community.aws.ec2_vpc_nacl](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_nacl_module.rst)|create and delete Network ACLs.
[community.aws.ec2_vpc_nacl_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_nacl_info_module.rst)|Gather information about Network ACLs in an AWS VPC
[community.aws.ec2_vpc_nat_gateway](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_nat_gateway_module.rst)|Manage AWS VPC NAT Gateways.
[community.aws.ec2_vpc_nat_gateway_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_nat_gateway_info_module.rst)|Retrieves AWS VPC Managed Nat Gateway details using AWS methods.
[community.aws.ec2_vpc_peer](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_peer_module.rst)|create, delete, accept, and reject VPC peering connections between two VPCs.
[community.aws.ec2_vpc_peering_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_peering_info_module.rst)|Retrieves AWS VPC Peering details using AWS methods.
[community.aws.ec2_vpc_route_table](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_route_table_module.rst)|Manage route tables for AWS virtual private clouds
[community.aws.ec2_vpc_route_table_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_route_table_info_module.rst)|Gather information about ec2 VPC route tables in AWS
[community.aws.ec2_vpc_vgw](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_vgw_module.rst)|Create and delete AWS VPN Virtual Gateways.
[community.aws.ec2_vpc_vgw_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_vgw_info_module.rst)|Gather information about virtual gateways in AWS
[community.aws.ec2_vpc_vpn](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_vpn_module.rst)|Create, modify, and delete EC2 VPN connections.
[community.aws.ec2_vpc_vpn_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_vpc_vpn_info_module.rst)|Gather information about VPN Connections in AWS.
[community.aws.ec2_win_password](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ec2_win_password_module.rst)|Gets the default administrator password for ec2 windows instances
[community.aws.ecs_attribute](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_attribute_module.rst)|manage ecs attributes
[community.aws.ecs_cluster](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_cluster_module.rst)|Create or terminate ECS clusters.
[community.aws.ecs_ecr](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_ecr_module.rst)|Manage Elastic Container Registry repositories
[community.aws.ecs_service](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_service_module.rst)|Create, terminate, start or stop a service in ECS
[community.aws.ecs_service_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_service_info_module.rst)|List or describe services in ECS
[community.aws.ecs_tag](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_tag_module.rst)|create and remove tags on Amazon ECS resources
[community.aws.ecs_task](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_task_module.rst)|Run, start or stop a task in ecs
[community.aws.ecs_taskdefinition](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_taskdefinition_module.rst)|register a task definition in ecs
[community.aws.ecs_taskdefinition_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.ecs_taskdefinition_info_module.rst)|Describe a task definition in ECS
[community.aws.efs](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.efs_module.rst)|create and maintain EFS file systems
[community.aws.efs_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.efs_info_module.rst)|Get information about Amazon EFS file systems
[community.aws.elasticache](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elasticache_module.rst)|Manage cache clusters in Amazon ElastiCache
[community.aws.elasticache_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elasticache_info_module.rst)|Retrieve information for AWS ElastiCache clusters
[community.aws.elasticache_parameter_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elasticache_parameter_group_module.rst)|Manage cache parameter groups in Amazon ElastiCache.
[community.aws.elasticache_snapshot](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elasticache_snapshot_module.rst)|Manage cache snapshots in Amazon ElastiCache
[community.aws.elasticache_subnet_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elasticache_subnet_group_module.rst)|manage ElastiCache subnet groups
[community.aws.elb_application_lb](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_application_lb_module.rst)|Manage an Application Load Balancer
[community.aws.elb_application_lb_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_application_lb_info_module.rst)|Gather information about application ELBs in AWS
[community.aws.elb_classic_lb](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_classic_lb_module.rst)|Creates or destroys Amazon ELB.
[community.aws.elb_classic_lb_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_classic_lb_info_module.rst)|Gather information about EC2 Elastic Load Balancers in AWS
[community.aws.elb_instance](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_instance_module.rst)|De-registers or registers instances from EC2 ELBs
[community.aws.elb_network_lb](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_network_lb_module.rst)|Manage a Network Load Balancer
[community.aws.elb_target](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_target_module.rst)|Manage a target in a target group
[community.aws.elb_target_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_target_group_module.rst)|Manage a target group for an Application or Network load balancer
[community.aws.elb_target_group_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_target_group_info_module.rst)|Gather information about ELB target groups in AWS
[community.aws.elb_target_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.elb_target_info_module.rst)|Gathers which target groups a target is associated with.
[community.aws.execute_lambda](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.execute_lambda_module.rst)|Execute an AWS Lambda function
[community.aws.iam](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_module.rst)|Manage IAM users, groups, roles and keys
[community.aws.iam_cert](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_cert_module.rst)|Manage server certificates for use on ELBs and CloudFront
[community.aws.iam_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_group_module.rst)|Manage AWS IAM groups
[community.aws.iam_managed_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_managed_policy_module.rst)|Manage User Managed IAM policies
[community.aws.iam_mfa_device_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_mfa_device_info_module.rst)|List the MFA (Multi-Factor Authentication) devices registered for a user
[community.aws.iam_password_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_password_policy_module.rst)|Update an IAM Password Policy
[community.aws.iam_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_policy_module.rst)|Manage inline IAM policies for users, groups, and roles
[community.aws.iam_policy_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_policy_info_module.rst)|Retrieve inline IAM policies for users, groups, and roles
[community.aws.iam_role](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_role_module.rst)|Manage AWS IAM roles
[community.aws.iam_role_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_role_info_module.rst)|Gather information on IAM roles
[community.aws.iam_saml_federation](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_saml_federation_module.rst)|Maintain IAM SAML federation configuration.
[community.aws.iam_server_certificate_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_server_certificate_info_module.rst)|Retrieve the information of a server certificate
[community.aws.iam_user](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_user_module.rst)|Manage AWS IAM users
[community.aws.iam_user_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.iam_user_info_module.rst)|Gather IAM user(s) facts in AWS
[community.aws.kinesis_stream](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.kinesis_stream_module.rst)|Manage a Kinesis Stream.
[community.aws.lambda](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lambda_module.rst)|Manage AWS Lambda functions
[community.aws.lambda_alias](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lambda_alias_module.rst)|Creates, updates or deletes AWS Lambda function aliases
[community.aws.lambda_event](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lambda_event_module.rst)|Creates, updates or deletes AWS Lambda function event mappings
[community.aws.lambda_facts](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lambda_facts_module.rst)|Gathers AWS Lambda function details as Ansible facts
[community.aws.lambda_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lambda_info_module.rst)|Gathers AWS Lambda function details
[community.aws.lambda_policy](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lambda_policy_module.rst)|Creates, updates or deletes AWS Lambda policy statements.
[community.aws.lightsail](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.lightsail_module.rst)|Manage instances in AWS Lightsail
[community.aws.rds](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_module.rst)|create, delete, or modify Amazon rds instances, rds snapshots, and related facts
[community.aws.rds_instance](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_instance_module.rst)|Manage RDS instances
[community.aws.rds_instance_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_instance_info_module.rst)|obtain information about one or more RDS instances
[community.aws.rds_param_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_param_group_module.rst)|manage RDS parameter groups
[community.aws.rds_snapshot](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_snapshot_module.rst)|manage Amazon RDS snapshots.
[community.aws.rds_snapshot_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_snapshot_info_module.rst)|obtain information about one or more RDS snapshots
[community.aws.rds_subnet_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.rds_subnet_group_module.rst)|manage RDS database subnet groups
[community.aws.redshift](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.redshift_module.rst)|create, delete, or modify an Amazon Redshift instance
[community.aws.redshift_cross_region_snapshots](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.redshift_cross_region_snapshots_module.rst)|Manage Redshift Cross Region Snapshots
[community.aws.redshift_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.redshift_info_module.rst)|Gather information about Redshift cluster(s)
[community.aws.redshift_subnet_group](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.redshift_subnet_group_module.rst)|manage Redshift cluster subnet groups
[community.aws.route53](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.route53_module.rst)|add or delete entries in Amazons Route 53 DNS service
[community.aws.route53_health_check](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.route53_health_check_module.rst)|Add or delete health-checks in Amazons Route53 DNS service
[community.aws.route53_info](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.route53_info_module.rst)|Retrieves route53 details using AWS methods
[community.aws.route53_zone](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.route53_zone_module.rst)|add or delete Route53 zones
[community.aws.s3_bucket_notification](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.s3_bucket_notification_module.rst)|Creates, updates or deletes S3 Bucket notification for lambda
[community.aws.s3_lifecycle](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.s3_lifecycle_module.rst)|Manage s3 bucket lifecycle rules in AWS
[community.aws.s3_logging](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.s3_logging_module.rst)|Manage logging facility of an s3 bucket in AWS
[community.aws.s3_metrics_configuration](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.s3_metrics_configuration_module.rst)|Manage s3 bucket metrics configuration in AWS
[community.aws.s3_sync](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.s3_sync_module.rst)|Efficiently upload multiple files to S3
[community.aws.s3_website](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.s3_website_module.rst)|Configure an s3 bucket as a website
[community.aws.sns](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.sns_module.rst)|Send Amazon Simple Notification Service messages
[community.aws.sns_topic](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.sns_topic_module.rst)|Manages AWS SNS topics and subscriptions
[community.aws.sqs_queue](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.sqs_queue_module.rst)|Creates or deletes AWS SQS queues
[community.aws.sts_assume_role](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.sts_assume_role_module.rst)|Assume a role using AWS Security Token Service and obtain temporary credentials
[community.aws.sts_session_token](https://github.com/ansible-collections/community.aws/blob/main/docs/community.aws.sts_session_token_module.rst)|Obtain a session token from the AWS Security Token Service

<!--end collection content-->

## Installing this collection

You can install the AWS collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install community.aws

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: community.aws

```

A specific version of the collection can be installed by using the `version` keyword in the `requirements.yml` file:

```yaml
---
collections:
  - name: community.aws
    version: 0.1.1
```

You can either call modules by their Fully Qualified Collection Namespace (FQCN), such as `community.aws.ec2_instance`, or you can call modules by their short name if you list the `community.aws` collection in the playbook's `collections` keyword:

```yaml
---
  - name: Create a DB instance using the default AWS KMS encryption key
    community.aws.rds_instance:
      id: test-encrypted-db
      state: present
      engine: mariadb
      storage_encrypted: True
      db_instance_class: db.t2.medium
      username: "{{ username }}"
      password: "{{ password }}"
      allocated_storage: "{{ allocated_storage }}"

```


### See Also:

* [Amazon Web Services Guide](https://docs.ansible.com/ansible/latest/scenario_guides/guide_aws.html)
* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Community AWS collection repository](https://github.com/ansible-collections/community.aws).

You can also join us on:

- Freenode IRC - ``#ansible-aws`` Freenode channel

### More information about contributing

- [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) - Details on contributing to Ansible
- [Contributing to Collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) - How to check out collection git repositories correctly
- [Guidelines for Ansible Amazon AWS module development](https://docs.ansible.com/ansible/latest/dev_guide/platforms/aws_guidelines.html)
- [Getting Started With AWS Ansible Module Development and Community Contribution](https://www.ansible.com/blog/getting-started-with-aws-ansible-module-development)

## Release notes
<!--Add a link to a changelog.rst file or an external docsite to cover this information. -->

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collection Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
