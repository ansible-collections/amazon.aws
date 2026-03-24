---
name: changelog
description: Create or update changelog fragments for documenting changes
---

<!--
This skill is the single source of truth for changelog fragment management.
It can create new fragments, analyze changes to suggest content, and update
fragments with PR URLs after pull request creation.

All pull requests require a changelog fragment in changelogs/fragments/.
-->

# Changelog Fragment Workflow

This skill has two modes: **create** (default) and **update-pr-url**.

## Mode: Create Fragment

Create a new changelog fragment to document changes:

1. **Analyze current changes** (optional but recommended):
   - Run `git status` to see uncommitted/staged changes
   - Run `git diff origin/main...HEAD --name-only` to see files changed in branch
   - Run `git log origin/main..HEAD --oneline` to see commit messages
   - Based on this analysis, suggest:
     - Change type (infer from file paths and commit messages)
     - Affected components (from modified file paths)
     - Description (synthesize from commit messages)
   - Present suggestions to the user for confirmation/editing

2. **Determine the change type** (if not auto-detected):
   - `bugfixes`: Bug fixes and corrections
   - `minor_changes`: New features, enhancements, or improvements
   - `major_changes`: Significant new functionality or major updates
   - `breaking_changes`: Changes that break backwards compatibility
   - `deprecated_features`: Features marked as deprecated
   - `removed_features`: Features that have been removed
   - `security_fixes`: Security vulnerability fixes
   - `trivial`: Trivial changes like typos, test additions, or refactoring (not user-facing)

3. **Gather details from user**:
   - Confirm or edit the suggested change type
   - Confirm or edit the affected component/module (e.g., `ec2_instance`, `s3_bucket`, `aws_ssm connection plugin`)
   - Confirm or edit the description (1-2 sentences, user-facing perspective)
   - Confirm or provide issue/PR number if applicable

4. **Generate filename**:
   - If PR/issue number provided: `<number>-<brief-slug>.yml` (e.g., `2869-ssm-connection-fix.yml`)
   - Otherwise: `<brief-slug>.yml` (e.g., `plugin-utils-inventory-unittests.yml`)
   - Use lowercase, hyphens for spaces, keep it concise

5. **Create the fragment file** in `changelogs/fragments/`:
   ```yaml
   <change_type>:
     - <component> - <description> (https://github.com/ansible-collections/amazon.aws/pull/XXXX).
   ```

   **Examples**:
   ```yaml
   bugfixes:
     - ec2_instance - Fixed issue where tags were not properly applied during instance creation (https://github.com/ansible-collections/amazon.aws/pull/1234).
   ```

   ```yaml
   minor_changes:
     - s3_bucket - Add support for intelligent tiering configuration (https://github.com/ansible-collections/amazon.aws/pull/5678).
     - s3_bucket - Add validation for bucket name format (https://github.com/ansible-collections/amazon.aws/pull/5678).
   ```

   **Multiple sections**:
   ```yaml
   minor_changes:
     - plugin_utils/inventory - Extract role session name generation into separate method (https://github.com/ansible-collections/amazon.aws/pull/2902).
   trivial:
     - plugin_utils/inventory - Add unit tests for region handling (https://github.com/ansible-collections/amazon.aws/pull/2902).
   ```

6. **Important notes**:
   - If PR number is unknown, use `XXXX` as placeholder - use the **update-pr-url** mode after PR creation
   - Each entry should be from a user's perspective (what changed, not how it was implemented)
   - End each entry with a full stop before the PR link
   - The PR URL is required even for trivial changes
   - For changes affecting multiple components, create separate entries under the same section

7. **Confirm with the user**:
   - Show the filename and content
   - Ask if they want to proceed with creating the file
   - Create the file only after confirmation

## Mode: Update PR URL

Update existing changelog fragments with the PR URL after pull request creation.
This mode is called automatically by the `create-pr` skill.

**Usage**: When invoked with a PR number (e.g., "update changelog fragments with PR 1234"):

1. **Find changelog fragments**:
   - List all files in `changelogs/fragments/` that are part of current changes
   - Run `git diff origin/main...HEAD --name-only | grep 'changelogs/fragments/'`
   - Filter to only `.yml` and `.yaml` files

2. **Check each fragment**:
   - Read the fragment file
   - Check if it contains `XXXX` or no github.com URL
   - If it needs updating, proceed to step 3

3. **Update the fragment**:
   - Replace `XXXX` with the actual PR number
   - If no URL exists, add it: `(https://github.com/ansible-collections/amazon.aws/pull/<pr-number>).`
   - Preserve the existing format and structure
   - Write the updated content back to the file

4. **Commit and push**:
   - If any fragments were updated:
     - Stage the updated fragments: `git add changelogs/fragments/`
     - Commit with message: "Update changelog fragments with PR URL"
     - Push to the current branch
   - Report which fragments were updated

**Important**:
- Only update fragments that contain `XXXX` or are missing github.com URLs
- Don't update fragments that already have a valid PR URL
- Preserve the original YAML structure and formatting
