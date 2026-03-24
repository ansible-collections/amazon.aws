# Reliability Fixes Workflow

Fetch reliability issues from SonarCloud, analyse them, suggest fixes, and implement approved fixes grouped by severity and type.

## Overview

This skill pulls reliability issues (bugs) from the SonarCloud API for the ansible-collections/amazon.aws project, groups them by severity and issue type, analyses the code, suggests fixes, and creates focused PRs for review.

## Workflow

### 1. Fetch Reliability Issues

Retrieve unresolved reliability issues from SonarCloud:

```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=BUG&resolved=false&ps=500"
```

Parse the JSON response to extract:
- Total count of issues
- List of issues with: key, component (file path), severity, type, line, message, rule, tags
- Component details

### 2. Group by Severity and Type

Group the issues by `severity` field and analyse by rule/tag patterns. Severity levels:
- `BLOCKER` - Blocker bugs that must be fixed immediately
- `CRITICAL` - Critical bugs
- `MAJOR` - Major bugs
- `MINOR` - Minor bugs
- `INFO` - Informational issues

Additionally, analyse common issue patterns:
- Null pointer dereference
- Resource leaks
- Exception handling issues
- Logic errors
- Type errors
- Unused code

For each severity level, create a summary showing:
- Severity level and count
- Number of issues
- Affected files
- Rule types involved
- Common patterns

### 3. Present Issues to User

Display a summary table of all issues grouped by severity:

```
Reliability Issues Summary (Unresolved only)
============================================

Severity    | Count | Common Rules                      | Files Affected
------------|-------|-----------------------------------|---------------
BLOCKER     |   0   | -                                 | -
CRITICAL    |   2   | python:S1862, python:S3776        | module1.py, module2.py
MAJOR       |   15  | python:S112, python:S1135         | various
MINOR       |   8   | python:S1481, python:S125         | various
```

Ask the user which severity level or specific rule they want to address first.

### 4. Analyse and Suggest Fixes

For the selected group:

**Step 4.1: Read Affected Files**
- Use the Read tool to read each affected file
- Focus on the specific line numbers mentioned in the issues

**Step 4.2: Analyse Each Issue**
For each issue in the group:
- Display the issue details:
  - File and line number
  - SonarCloud message
  - Rule key and link to rule documentation
  - Code snippet showing the problematic line(s)
- Analyse the context:
  - Read surrounding code to understand intent
  - Check if this is a false positive
  - Consider project patterns and standards
  - Understand the potential impact of the bug
- Suggest a fix:
  - Provide specific code changes
  - Explain why this fix is appropriate
  - Note any potential side effects
  - Consider if this is actually safe to ignore vs needs fixing
  - For complexity issues: focus on extracting logic that can be cleanly unit-tested

**Step 4.3: Group Fixes by Approach**
Group suggested fixes into logical units:
- If multiple issues in the same file can be fixed together, group them
- If issues require the same type of change, group them
- Keep groups small enough to be reviewable (prefer multiple small PRs over one large PR)

### 5. Get User Approval

Present all suggested fixes for the group and ask:
- Which fixes should be implemented?
- Which fixes should be marked as false positives/won't fix?
- Which fixes need more investigation?

Use AskUserQuestion to let the user select:
- "Implement all suggested fixes"
- "Implement selected fixes" (then ask which ones)
- "Skip this group"
- "Mark as won't fix" (for false positives or accepted issues)

### 6. Implement Approved Fixes

For each approved fix:

**Step 6.1: Create Feature Branch**
- Check current branch (should be on main)
- Create a descriptive branch name: `reliability/<rule-or-category>` (e.g., `reliability/exception-handling`)
- Base the branch off origin/main

**Step 6.2: Apply Fixes**
- Use the Edit tool to apply each fix
- Add comments where helpful to explain reliability-related changes
- Ensure fixes follow project coding standards

**Step 6.3: Run Pre-commit Checks**
- Use the `precommit` skill to run format, lint, and unit tests
- If checks fail, analyse failures:
  - If formatting issues, let formatter fix them
  - If test failures, investigate and fix
  - If issues can't be auto-resolved, report to user

**Step 6.4: Commit Changes**
- Create a descriptive commit message:
  ```
  Fix <rule/category> reliability issues

  - <file1>:<line> - <brief description of fix>
  - <file2>:<line> - <brief description of fix>

  Addresses <count> reliability issue(s) identified by SonarCloud:
  - <ruleKey>: <rule description>

  SonarCloud issue keys: <key1>, <key2>, ...
  ```
- Commit with project standards (GPG signing will be handled by user if needed)

**Step 6.5: Create Changelog Fragment**
- Use the `changelog` skill to create a fragment
- Suggested type: `bugfixes` (reliability issues are bugs)
- Description: "Fix <rule/category> reliability issues identified by SonarCloud"

### 7. Create Pull Request (Optional)

Ask user if they want to create a PR now or continue with more issues:
- If create PR now:
  - Use the `create-pr` skill to create a draft PR
  - PR title: "Fix <severity/rule> reliability issues"
  - PR body should include:
    - List of issues addressed
    - Links to SonarCloud issue details
    - Description of fixes applied
    - Note that SonarCloud will re-analyse after merge
- If continue:
  - Return to step 3 to select another group
  - User can create a combined PR for multiple issues later

### 8. Close Issues (Automatic)

**Note**: SonarCloud issues are automatically closed when:
1. The code fix is merged and SonarCloud re-analyses the project
2. The issue is no longer detected in the updated code

For false positives or won't fix issues, user can:
- Go to SonarCloud UI: https://sonarcloud.io/project/issues?id=ansible-collections_amazon.aws&types=BUG
- Find the issue by key or file/line
- Mark as "Won't Fix" or "False Positive" with a comment explaining why

## Important Notes

### API Limitations
- Maximum page size is 500 issues per request
- Use pagination parameters (`p` and `ps`) for larger result sets
- No authentication required for public projects (read-only)
- Issue resolution can only be changed via authenticated API calls or web UI

### Fix Strategies by Common Rule Types

**python:S1862** (Duplicate branch in conditional):
- Refactor conditional logic to remove duplicates
- May indicate copy-paste errors
- Check if different conditions should have different logic

**python:S3776** (Cognitive complexity too high):
- Refactor complex functions into smaller units
- **Prioritise extracting logic that can be cleanly unit-tested**
- Look for self-contained chunks of logic that can be broken out
- Extract nested logic into helper functions
- Simplify conditional statements
- Consider whether extracted functions can be tested without mocking the module or client

**python:S112** (Generic exception raised):
- Replace generic exceptions with specific exception types
- Consider creating custom exception classes where appropriate
- Maintain backwards compatibility

**python:S1135** (TODO/FIXME tags):
- Implement the TODO if straightforward
- Create issues for complex TODOs
- Remove obsolete TODOs

**python:S1481** (Unused local variables):
- Remove if truly unused
- Check if this indicates incomplete implementation
- Prefix with `_` if intentionally unused

**python:S125** (Commented-out code):
- Remove if no longer needed
- Convert to documentation if explaining removed functionality
- Uncomment and fix if still relevant

**Exception handling issues**:
- Ensure all exceptions are properly caught and handled
- Avoid bare `except:` clauses
- Log exceptions appropriately
- Don't silently ignore errors

### Testing Requirements
- All reliability fixes MUST pass precommit checks
- Pay special attention to unit tests that might rely on specific behaviour
- Consider adding tests for bug fixes to prevent regression
- Integration tests may be needed for some fixes

### Review Considerations
- Reliability fixes should be reviewed carefully by maintainers
- Each PR should be focused on one type of issue or severity level
- Include rationale for why each fix is safe
- Document any issues that are false positives or won't fix
- Link to SonarCloud rule documentation
- Consider the impact on existing behaviour

## Example Usage

User: "Run the reliability-fixes skill"

Skill:
1. Fetches 127 total issues, 25 unresolved
2. Groups into severity levels
3. Shows summary table
4. User selects "CRITICAL"
5. Analyses 2 critical issues
6. Suggests fixes for duplicate branch logic
7. User approves fixes
8. Creates branch `reliability/duplicate-branches`
9. Applies fixes, runs tests, commits
10. Creates changelog fragment
11. Asks about PR creation
12. User says "create PR"
13. Creates draft PR with details
14. Returns to severity/rule selection for remaining issues

## Future Enhancements

- Support for authenticated API calls to mark issues as won't fix
- Integration with GitHub to auto-link PR to SonarCloud analysis
- Automatic detection of false positives based on context
- Support for custom fix patterns per rule type
- Grouping by tags or rule categories for better organisation
- Support for filtering by file path patterns
