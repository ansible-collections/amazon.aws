---
name: create-pr
description: Create a draft pull request with all required checks and formatting
---

<!--
This is a skill rather than a slash command because it needs to execute
multiple bash commands and tools that require explicit permission.

By defining this as a skill, we can reference it in CLAUDE.md workflows and
ensure consistent PR creation with all required checks and template formatting.
-->

# Create Pull Request Workflow

Create a draft pull request following project standards:

## Pre-flight Checks

1. **Verify branch**: Ensure we're not on the main branch
   - If on main, stop and warn the user
   - Display current branch name

2. **Check git status**: Verify all changes are committed
   - Run `git status` to check for uncommitted changes
   - If uncommitted changes exist, ask the user if they want to proceed anyway
   - If user declines, stop

3. **Check for changelog fragments**: Unless user explicitly requests a skip-changelog PR
   - Run `git diff origin/main...HEAD --name-only` to see changed files
   - Check if changes are only in: `changelogs/fragments/`, `.github/`, or `tests/`
     - If yes, skip changelog requirement
   - For other changes:
     - Check if any files matching `changelogs/fragments/*.yml` or `changelogs/fragments/*.yaml` exist in branch
     - If changelog fragment exists:
       - Read it to verify it describes the current changes
       - If outdated, ask user if it should be updated
     - If no changelog fragment exists:
       - Ask: "No changelog fragment found. Would you like to create one?"
       - If yes: "Use the `changelog` skill to create a fragment, then re-run create-pr"
       - If no (user explicitly declines): Note this for step 8 to apply the `skip-changelog` label

4. **Run prepush checks**: Use the `prepush` skill unless it was run recently in this session
   - If prepush was already run with no code changes since, skip this step
   - Otherwise, run the full prepush workflow
   - If any checks fail, stop and report the failures
   - Only proceed if all checks pass

## Push to Remote

5. **Push branch to remote**: Ensure the current branch is pushed
   - Check if the branch is already tracking a remote and is up to date
   - If already pushed and up to date, skip this step
   - If not pushed or local is ahead:
     - Select remote according to any preferences in CLAUDE.md configuration
     - If no preference specified and multiple remotes available, ask which to use
     - Push with `git push -u <remote> <branch-name>`
   - If push fails, report the error and stop

## Analyse Changes and Generate PR Details

6. **Analyse changes and generate PR suggestions**:
   - Run `git log origin/main..HEAD` to see all commits in this branch
   - Run `git diff origin/main...HEAD --stat` to see file changes
   - Review changelog fragments (if any) for context
   - Based on this analysis, generate suggestions for:
     - **Title**: Derive from commits and changelog entries (concise, descriptive)
     - **Summary**: Synthesise from commit messages and changes (what changed and why, include "Fixes #nnn" if applicable)
     - **Issue type**: Infer from the nature of changes (Bugfix/Docs/Feature/New Module)
     - **Component name**: Extract from files changed (module, plugin, or feature name)
     - **Additional info**: Any relevant context from commits or changes
   - Use AskUserQuestion to present these suggestions and allow the user to override any of them

## Create Pull Request

7. **Create draft PR**: Create a draft PR to ansible-collections/amazon.aws with the template:
   ```
   ##### SUMMARY
   <user-provided or generated summary>

   <If fixing an issue: "Fixes #nnn">

   ##### ISSUE TYPE
   <Bugfix/Docs/Feature/New Module Pull Request>

   ##### COMPONENT NAME
   <user-provided or generated component name>

   ##### ADDITIONAL INFORMATION
   <user-provided or generated additional info, if any>

   Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>
   ```
   - Use `gh pr create --draft --repo ansible-collections/amazon.aws --title "..." --body "..."`
   - The Assisted-by line must NOT be commented out
   - Do NOT add a "Generated with Claude Code" line

8. **Apply labels**:
   - If this is a skip-changelog PR, apply "skip-changelog" label
   - If the changelog fragments contain a breaking_changes section, apply "do_not_backport" label
   - Use `gh pr edit <pr-number> --add-label <label> --repo ansible-collections/amazon.aws` for each label

## Post-PR Tasks

9. **Update changelog fragments**: Use the `changelog` skill in update-pr-url mode
   - Parse the PR number from the gh pr create output
   - Invoke the `changelog` skill with: "update changelog fragments with PR <number>"
   - The changelog skill will handle finding, updating, committing, and pushing fragments

10. **Report success**: Display:
   - PR URL
   - PR number
   - Labels applied (if any)
   - Whether changelog fragments were updated
   - Next steps (if any)

**Important**:
- Always create as draft PR
- Always target ansible-collections/amazon.aws repository
- Always include the Assisted-by line (NOT commented out)
- Never add a "Generated with" line
- Use the `changelog` skill for all changelog fragment operations
- If changelog is missing, prompt user to run `changelog` skill before continuing
