# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Note: If you're updating MODULES, PLUGINS probably needs updating too.

    # Formatted for Modules
    # - modules don't support 'env'
    MODULES = r"""
options: {}
"""

    # Formatted for non-module plugins
    # - modules don't support 'env'
    PLUGINS = r"""
options:
  assume_role_arn:
    description:
      - The ARN of the IAM role to assume to perform the lookup.
      - You should still provide AWS credentials with enough privilege to perform the AssumeRole action.
    aliases: ["iam_role_arn"]
"""
