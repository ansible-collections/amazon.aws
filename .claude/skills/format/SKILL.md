---
name: format
description: Run code formatting with black standards
---

<!--
This is a skill rather than a slash command because Claude CLI cannot execute
commands (like tox) by default without explicit permission.

By defining this as a skill, we can reference it in workflows and run it independently.
-->

# Format Workflow

Run code formatting to apply black formatting standards:

1. **Format the code**: Run `tox -m format` to apply black formatting standards
   - Report any files that were reformatted
   - If no files were changed, report that formatting is already correct

2. **Provide summary**: Give a brief summary of:
   - Number of files reformatted (if any)
   - Whether the code is properly formatted

**Important**: This skill only formats code. It does not commit changes automatically.
