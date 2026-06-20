# Workflow

Between steps in your work, commit any changes to git.
Git commits should be made regularly to make reviews easier.

**Before committing:**
- Run the `precommit` skill to run format, lint, and unit tests

**Before pushing:**
- Run the `prepush` skill to run format, lint, unit tests (newest and oldest), sanity tests, and optionally integration tests
- Ensure a changelog fragment exists (use the `changelog` skill to create one)

**Creating a pull request:**
- Use the `changelog` skill to create a changelog fragment if not already done
- Use the `create-pr` skill to create the PR (handles prepush checks, pushing to remote, and updating changelog fragments)

**Individual steps:**
- Format: `format` skill
- Lint: `lint` skill
- Unit tests: `unit-tests` skill (runs newest by default, specify "oldest" for oldest supported versions)
- Sanity tests: `sanity-tests` skill
- Integration tests: `integration-tests` skill (requires AWS credentials, creates real resources)
- Security fixes: `security-fixes` skill (fetch and fix SonarCloud security hotspots)

# Code Style
This project uses the black formatting standards.
As a type hint, prefer ClientType over RetryingBotoClientWrapper unless "aws_retry" is used as a parameter. RetryingBotoClientWrapper is just a decorator around boto3.Client and is not always needed.
When adding typing hints, also use `from __future__ import annotations` and wrap the necessary type imports in an `if typing.TYPE_CHECKING` block.
In modules, `from __future__` imports are the only imports permitted before the DOCUMENTATION, EXAMPLES, and RETURN definitions; all other imports must come after these definitions.
When adding docstrings, a docstring for main() can be skipped.
It is not necessary to mention that project standards have been followed in commit or pull request messages.
New code should include docstrings and type hints.
When refactoring to use error handling templates, refer to the s3 and elbv2 module code as preferred examples.
Never create '__init__.py' files under plugins/.
For "check_mode", prefer an early return pattern over a guard pattern.
New Python files should generally use the following boilerplate:
```python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
```
There are counter-examples; counter-examples should not be modified.

# Documentation
When adding new features (modules, plugins, parameters, return values, etc.), always include version_added tags in the documentation.
Use the `next-version` skill to determine the appropriate version number before adding version_added tags.
For new features, use the next minor version returned by the skill.

# Testing

**Unit tests:**
- When running unit tests, always use the `unit-tests` skill to run the full test suite rather than trying to limit to specific tests, there are some quirks that will result in test failures if you don't.
- Code in plugins/module_utils/, plugins/plugin_utils, and extensions/ should generally have unit tests.
- When refactoring code in plugins/modules/ consider options that make unit testing (without mocking client or module) simpler.

**Integration tests:**
- Use the `integration-tests` skill to run integration tests for specific modules or plugins.
- Integration tests are in tests/integration/targets/ and require AWS credentials.
- Test naming: modules use the module name, plugins use `<type>_<name>` (e.g., `lookup_aws_account_attribute`).

**General testing guidelines:**
- When testing or writing documentation, prefer RFC5737 and RFC3849 test/documentation addresses unless there's a need to do otherwise; confirm exceptions with the user.

# Pull Requests

All changes require a changelog fragment in `changelogs/fragments/` before creating a PR, except for changes only to `.github/`, `tests/`, or `changelogs/fragments/`.
Use the `changelog` skill to create changelog fragments for documenting changes.
Use the `create-pr` skill to create pull requests.
The `create-pr` skill will handle prepush checks, changelog validation, pushing to remote, creating the draft PR with the correct template and labels, and updating changelog fragments with the PR URL.

# Slash Commands

- `/check-actions` - Check GitHub Actions status for the current branch and suggest fixes for failures
- `/check-sonar` - Check SonarCloud analysis results for the current PR
- `/fix-sonarcloud-security` - Fetch and fix SonarCloud security hotspots by category
