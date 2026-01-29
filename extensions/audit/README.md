# Indirect Node Counts in Ansible Collections

## Overview

In the context of Ansible automation, **indirect node counts** refer to the practice of verifying capacity or availability **by analyzing the output of Ansible modules that interact with external systems**, rather than directly querying the nodes themselves. This approach is especially useful in complex, public cloud, or on-premises environments.

This file explains:
- What indirect node counts are
- Why they are required
- What they enable
- Their value

## What Are Indirect Node Counts?

Standard node counting relies on Ansible connecting to a host. However, in cloud or API-driven automation, the "managed nodes" are often manipulated via a centralized API (like AWS or Azure) rather than direct connections.

**Indirect node counts** solve this by inspecting the **return values (JSON payload)** of specific Ansible modules.

For example:
1. A playbook runs `amazon.aws.ec2_instance_info` to gather facts about your cloud environment.
2. The module queries the AWS API and returns a list of instances.
3. The controller applies a specific filter (defined in `extensions/audit/event_query.yml`) to that output to count how many unique nodes were automated.

This process is **passive**: it derives counts from the automation that is already running, without initiating separate API requests.

## Why Are They Required?

Directly connecting to every node:
- Is **inefficient** in large-scale environments
- May be **prohibited** due to security, network segmentation, or policy
- **Doesn't scale** across multiple clusters or providers
- Often leads to **incomplete or stale data**

Using indirect node counts via cluster managers:
- Enables **centralized insight** into resource usage
- Works well in **managed or disconnected environments**
- Allows **non-invasive** assessment (e.g., read-only API access)

## What Does It Do?

In practical terms, using indirect node counts in an Ansible collection:
- Enables **guardrails** to verify what you are automating
- Reduces operational risk and improves **predictability** of automation workflows

## Why This Is a Good Practice

| Benefit | Description |
|--------|-------------|
| ✅ Scalable | Works across many clusters and environments |
| ✅ Secure | Limits direct access to sensitive nodes |
| ✅ Efficient | Avoids per-node polling, uses cached or aggregated data |
| ✅ Integrated | Leverages our existing Certified and Validated collections |
| ✅ Reliable | Provides consistent data source for automation decisions |

## Supported Resources for Amazon Web Services (AWS)

The following table details the AWS resources currently supported by the NodeQuery logic within the **amazon.aws** collection. To ensure consistent reporting across different services, this extension maps service-specific attributes to a set of **Canonical Facts**.

**What are Canonical Facts?**
Canonical Facts are standardized fields (like `id`, `name`, `tags`, and `status`, and `status`) that provide a uniform way to identify and assess resources, regardless of the underlying AWS service. For example, whether querying an EC2 instance or a VPC, the unique identifier is always mapped to `id`.

**Note:** Not all resources support every fact. For example, a Route Table may only have an `id` and `tags`, while an EC2 instance will have all four.

The table below details how AWS resources are mapped to these canonical facts.

| Category | AWS Resource | Ansible Module | Canonical Fact Mapping |
| :--- | :--- | :--- | :--- |
| **Compute** | **EC2 Instance** | `ec2_instance_info` | `.instance_id` → **id**<br>`.state` → **status**<br>`(.name // .tags.Name)` → **name** <br>`.tags` → **tags**  |
| **Database** | **RDS Instance** | `rds_instance_info` | `.db_instance_identifier` → **name**<br>`.dbi_resource_id` → **id**<br>`.db_instance_status` → **status**<br>`.tags` → **tags**  |
| **Database** | **RDS Cluster** | `rds_cluster_info` | `db_cluster_identifier` → **name**<br>`.db_cluster_resource_id` → **id**<br>`.status` → **status**<br>`.tags` → **tags** |
| **Storage** | **S3 Bucket** | `s3_bucket_info` | `.name` → **name**<br>`.bucket_tagging` → **tags** |
| **Storage** | **S3 Object** | `s3_object_info` | `.object_name` → **name**<br>`.object_tagging` → **tags** |
| **Networking** | **Application / Network LB** | `elb_application_lb_info` | `.load_balancer_name` → **name**<br>`state` → **status** |
| **Networking** | **Classic Load Balancer** | `elb_classic_lb_info` | `.load_balancer_name` → **name**<br>|
| **Networking** | **VPC** | `ec2_vpc_net_info` | `id` → **id**<br>`state` → **status**<br>`.tags` → **tags** |
| **Networking** | **VPC Subnet** | `ec2_vpc_subnet_info` | `.id` → **id**<br>`.state` → **status**<br>`.tags` → **tags** |
| **Networking** | **NAT Gateway** | `ec2_vpc_nat_gateway_info` | `.nat_gateway_id` → **id**<br>`state` → **status**<br>`.tags` → **tags** |
| **Networking** | **Internet Gateway** | `ec2_vpc_igw_info` | `.internet_gateway_id` → **id**<br>`.attachments.state` → **status**<br>`.tags` → **tags** |
| **Networking** | **Virtual Private Gateway** | `ec2_vpc_vgw_info` | `.vpn_gateway_id` → **id**<br>`.state` → **status**<br>`.tags` → **tags** |
| **Networking** | **Route Table** | `ec2_vpc_route_table_info` | `.route_table_id` → **id**<br>`.tags` → **tags** |
| **Networking** | **VPC Peering Connection** | `ec2_vpc_peering_info` | `.vpc_peering_connection_id` → **id**<br>`.state.code` → **status**<br>`.tags` → **tags**|
| **Networking** | **VPN Connection** | `ec2_vpc_vpn_info` | `.vpn_connection_id` → **id**<br>`.state` → **status**<br>`.tags` → **tags** |

## Testing and Validation

Reliability is ensured through integration testing. The **extensions/audit/event_query.yml** file is explicitly tested in this collection to verify that the node counting logic works as expected against the supported resources.

### How to Run Integration Tests Locally

To validate the node counting logic yourself, you can run any integration test target prefixed with **node_query_**.

#### Prerequisites
The indirect node counts integration tests have additional dependencies, specifically the `jq` Python bindings. Please run `pip install -r tests/integration/requirements.txt` to ensure all requirements are installed."

#### Command
**Example: Running the Networking Node Query Test**

```bash
ansible-test integration node_query_networking --no-temp-workdir
```

**Important: Critical Note: The **--no-temp-workdir** Flag**

When running these tests locally, you must include the **--no-temp-workdir** flag.

- **The Problem**: The tests rely on a local helper role, **setup_node_query**, to prepare the environment. Standard **ansible-test** behavior creates a temporary, isolated testing directory that does not automatically copy this helper role (as it is not a production dependency listed in **meta/main.yml**).

- **The Solution**: The **--no-temp-workdir** flag forces **ansible-test** to run in the current directory context, ensuring the test suite can access the **setup_node_query** role.
