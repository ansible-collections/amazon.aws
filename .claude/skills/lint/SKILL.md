---
name: lint
description: Run linting checks for code quality
---

<!--
This is a skill rather than a slash command because Claude CLI cannot execute
commands (like tox) by default without explicit permission.

By defining this as a skill, we can reference it in workflows and run it independently.
-->

# Lint Workflow

Run linting to check for code quality issues:

1. **Run linting**: Run `tox -m lint` to check for code quality issues
   - If linting fails, report the issues with details
   - If linting passes, report success

2. **Provide summary**: Give a brief summary of:
   - Linting status (pass/fail)
   - Any issues found (if failed)
   - Whether the code passes quality checks

**Important**: This skill only checks code quality. It does not fix issues or commit changes automatically.
