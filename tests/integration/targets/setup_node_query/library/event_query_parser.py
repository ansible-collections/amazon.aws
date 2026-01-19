#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: event_query_parser
short_description: Extract node query from event_query.yml file.
description:
  - Extract node query from event_query.yml file.
  - This module is used for integration tests for the collection amazon.aws only.
author:
  - "Aubin Bikouo (@abikouo)"
options:
  path:
    description:
      - The path to the extensions/audit/event_query.yml file to be parsed.
    type: str
    required: true
"""

EXAMPLES = r"""
"""

RETURN = r"""
node_queries:
    description: A dictionary of node queries extracted from the input file.
    returned: always
    type: dict
    sample:
        {
          "s3_bucket_info":
            '.buckets[] | select(. != null) |
                canonical_facts: {
                    name: .name,
                    tags: (.bucket_tagging // {})
                },
                facts: {
                    infra_type: "PublicCloud",
                    infra_bucket: "Storage",
                    device_type: "Bucket"
                }
            }'
        }
"""

try:
    import yaml
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule


def parse_event_queries(path: str) -> dict:
    result = {}
    with open(path, "rb") as f:
        content = list(yaml.safe_load_all(f))
        result = {k.split(".")[2]: v["query"] for k, v in content[0].items()}
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type="str", required=True),
        ),
        supports_check_mode=True,
    )

    path = module.params.get("path")
    module.exit_json(node_queries=parse_event_queries(path))


if __name__ == "__main__":
    main()
