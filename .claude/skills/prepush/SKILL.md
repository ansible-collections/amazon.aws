---
name: prepush
description: Run complete pre-push checks (format, lint, unit tests, sanity tests, optionally integration tests) before pushing code
---

<!--
This is a skill rather than a slash command because Claude CLI cannot execute
commands (like tox, ansible-test) by default without explicit permission.

By defining this as a skill, we can reference it in CLAUDE.md workflows:
"Before pushing to GitHub, run the `prepush` skill to run format, lint, unit tests, sanity tests, and optionally integration tests."

If this were a slash command instead, Claude would encounter a permission error
when trying to execute the commands, as it lacks access to the Bash tool.
-->

# Pre-push Workflow

Run the complete pre-push workflow to ensure code quality before pushing:

**Changelog-only Changes**: If the only uncommitted changes are to files in `changelogs/fragments/`, you may skip all validation steps entirely. Changelog fragments don't affect code quality and don't need testing.

**Smart Step Execution**: You may skip steps that were recently completed in this session with no code changes since. For example:
- If `format` was just run and no code was modified after, skip formatting
- If `lint` passed recently with no changes since, skip linting
- Always run tests if code has changed, but you may skip if tests just passed with no changes

1. **Check for changelog fragments**: Verify changelog fragments exist for significant changes
   - Run `git diff origin/main...HEAD --name-only` to see all changed files
   - Check if changes are only in: `changelogs/fragments/`, `.github/`, or `tests/`
     - If yes, skip changelog check (these don't require changelog fragments)
   - For other changes:
     - Check if any files in `changelogs/fragments/` exist in the current branch
     - If no changelog fragments found:
       - Ask: "No changelog fragment found. Is this intentional (trivial change)?"
       - If user says no: "Run the `changelog` skill to create a changelog fragment, then re-run prepush"
       - If user says yes: Continue to validation steps

2. **Format the code**: Use the `format` skill to apply black formatting standards (unless just run with no changes since)
   - Report any files that were reformatted

3. **Run linting**: Use the `lint` skill to check for code quality issues (unless just run with no changes since)
   - If linting fails, report the issues and stop
   - If linting passes, continue to testing

4. **Run unit tests**: Use the `unit-tests` skill twice to test both oldest and newest supported environments (unless just run with no changes since)
   - First, use the `unit-tests` skill with newest supported versions (default behavior)
   - Then, use the `unit-tests` skill with oldest supported versions (explicitly request oldest)
   - Report the test results for both environments (number of tests, pass/fail)
   - If either test suite fails, show the failure details and stop

5. **Run sanity tests**: Use the `sanity-tests` skill to execute ansible-test sanity checks (unless just run with no changes since)
   - Report the sanity test results
   - If sanity tests fail, show the failure details

6. **Ask about integration tests**: Determine if integration tests should be run
   - Check `git diff origin/main...HEAD --name-only` to see what files changed
   - Analyze changes and prompt accordingly:
     - **Integration test changes** (tests/integration/targets/):
       - Identify which test targets were modified
       - Ask: "Changes detected in integration tests: [list]. Would you like to run these tests?"
     - **Shared code changes** (plugins/plugin_utils/, plugins/module_utils/):
       - Ask: "Changes detected in shared code (plugin_utils/module_utils). Which integration tests should be run, if any?"
     - **Module/plugin changes** (plugins/modules/, plugins/connection/, plugins/lookup/, etc.):
       - Identify relevant integration tests based on changed files
       - Ask: "Integration tests available for: [list]. Would you like to run these tests?"
   - If user wants to run tests:
     - Use the `integration-tests` skill to run the selected tests
     - Report the integration test results
     - If integration tests fail, show the failure details
   - Note: Integration tests require AWS credentials and create real resources

7. **Provide summary**: Give a final summary of:
   - Changelog fragment status (present/not needed)
   - Which steps were run vs skipped
   - Formatting changes made (if run)
   - Linting status (if run)
   - Unit test results (if run)
   - Sanity test results (if run)
   - Integration test results (if run)
   - Whether the code is ready to push
   - Reminder: Use `changelog` skill if changelog fragment is needed

**Important**: Do NOT push automatically. Only validate the code and report the status so the user can review before pushing.

**Note**: Individual steps can be run using the `format`, `lint`, `unit-tests`, `sanity-tests`, and `integration-tests` skills.
