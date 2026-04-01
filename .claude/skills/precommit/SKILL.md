---
name: precommit
description: Run pre-commit checks (format, lint, unit tests) before committing code
---

<!--
This is a skill rather than a slash command because Claude CLI cannot execute
commands (like tox, pytest) by default without explicit permission.

By defining this as a skill, we can reference it in CLAUDE.md workflows:
"Before committing, run the `precommit` skill to run format, lint, and unit tests."

If this were a slash command instead, Claude would encounter a permission error
when trying to execute the commands, as it lacks access to the Bash tool.
-->

# Pre-commit Workflow

Run the complete pre-commit workflow to ensure code quality before committing:

1. **Format the code**: Use the `format` skill to apply black formatting standards
   - Report any files that were reformatted

2. **Run linting**: Use the `lint` skill to check for code quality issues
   - If linting fails, report the issues and stop
   - If linting passes, continue to testing

3. **Run unit tests**: Use the `unit-tests` skill to execute the full test suite with the newest supported versions
   - Report the test results (number of tests, pass/fail)
   - If tests fail, show the failure details

4. **Provide summary**: Give a final summary of:
   - Formatting changes made
   - Linting status
   - Test results
   - Whether the code is ready to commit

**Important**: Do NOT commit automatically. Only prepare the code and report the status so the user can review before committing.

**Note**: Individual steps can be run using the `format`, `lint`, and `unit-tests` skills.
