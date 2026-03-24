---
name: sanity-tests
description: Run ansible-test sanity checks
---

<!--
This is a skill rather than a slash command because Claude CLI cannot execute
commands (like ansible-test) by default without explicit permission.

By defining this as a skill, we can reference it in workflows and run it independently.
-->

# Sanity Tests Workflow

Run ansible-test sanity checks to validate Ansible-specific requirements:

1. **Run sanity tests**: Run `ansible-test sanity --docker` to execute ansible-test sanity checks
   - Report the sanity test results
   - If sanity tests fail, show the failure details with specific issues

2. **Provide summary**: Give a brief summary of:
   - Sanity test status (pass/fail)
   - Any issues found (if failed)
   - Whether the code passes Ansible sanity requirements

**Important**: This skill only runs sanity tests. It does not commit or fix issues automatically.

**Note**: Sanity tests check for Ansible-specific requirements like documentation format, imports, and other collection standards.
