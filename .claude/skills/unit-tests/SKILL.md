---
name: unit-tests
description: Run unit tests with tox (newest by default, or oldest when requested)
---

<!--
This is a skill rather than a slash command because Claude CLI cannot execute
commands (like tox, pytest) by default without explicit permission.

By defining this as a skill, we can reference it in workflows and run it independently.
-->

# Unit Tests Workflow

Run unit tests to validate code functionality:

1. **Determine which version to test**:
   - If the user explicitly asks for "oldest" supported versions, run `tox -m unit-oldest`
   - Otherwise, default to `tox -m unit-newest` (newest supported Ansible/Python versions)

2. **Run unit tests**: Execute the full test suite with the selected environment
   - Report the test results (number of tests, pass/fail)
   - If tests fail, show the failure details with specific test names and errors

3. **Provide summary**: Give a brief summary of:
   - Which environment was tested (oldest or newest)
   - Test results (passed/failed/skipped counts)
   - Any failures with details
   - Whether all tests passed

**Important**: This skill only runs tests. It does not commit changes automatically.

**Note**: For complete multi-environment testing (both oldest and newest supported versions), use the `prepush` skill instead.
