# Maintainability Fixes Workflow

Fetch maintainability issues (code smells) from SonarCloud, analyse them, suggest fixes, and implement approved fixes grouped by severity and type.

## Overview

This skill pulls maintainability issues (code smells) from the SonarCloud API for the ansible-collections/amazon.aws project, groups them by severity and issue type, analyses the code, suggests fixes, and creates focused PRs for review.

## Workflow

### 1. Fetch Maintainability Issues

Retrieve unresolved maintainability issues from SonarCloud:

```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&ps=500"
```

Parse the JSON response to extract:
- Total count of issues
- List of issues with: key, component (file path), severity, type, line, message, rule, tags
- Component details

### 2. Group by File and Severity

**Primary grouping**: Group the issues by `component` (file path), then by severity within each file.

Parse the component field to extract:
- Full file path
- File type (plugins/modules/, plugins/module_utils/, plugins/plugin_utils/, etc.)
- Basename for display

For each file, analyse:
- Total issue count
- Severity breakdown (BLOCKER/CRITICAL/MAJOR/MINOR/INFO)
- Rule types involved
- Common patterns in that file

Severity levels:
- `BLOCKER` - Blocker code smells that must be fixed immediately
- `CRITICAL` - Critical code smells
- `MAJOR` - Major code smells
- `MINOR` - Minor code smells
- `INFO` - Informational issues

Common issue patterns to identify:
- Cognitive complexity
- Code duplication
- Dead code
- Code organisation issues
- Documentation issues
- Naming conventions
- Code style issues

### 3. Present Issues to User

Display a summary table of all issues grouped by file, sorted by total issue count (highest first):

```
Maintainability Issues Summary (Unresolved only)
=================================================

File                                    | Total | CRIT | MAJOR | MINOR | Common Rules
----------------------------------------|-------|------|-------|-------|------------------
plugins/modules/ec2_instance.py         |   12  |   2  |   8   |   2   | S3776, S1192
plugins/module_utils/botocore.py        |   8   |   1  |   5   |   2   | S1066, S1192
plugins/modules/s3_bucket.py            |   5   |   0  |   3   |   2   | S1135, S125
...
```

Additionally, provide filtering options:
- Filter by file path pattern (e.g., "plugins/modules/*.py", "*/ec2_*.py")
- Filter by severity level (e.g., "CRITICAL and MAJOR only")
- Filter by rule type (e.g., "S3776 only")

Ask the user which file or filter they want to address first.

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
  - Understand the maintainability impact
- Suggest a fix:
  - Provide specific code changes
  - Explain why this fix improves maintainability
  - Note any potential side effects
  - Consider if this is actually safe to ignore vs needs fixing
  - For complexity issues: focus on extracting logic that can be cleanly unit-tested

**Step 4.3: Present All Issues for the File**
Since issues are grouped by file, present all issues found in the selected file:
- List each issue with line number, severity, rule, and message
- Show how issues relate to each other (e.g., multiple complexity issues in same function)
- Provide fix suggestions for each issue
- Note which issues can be addressed together as part of the same refactoring

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
- Create a descriptive branch name based on the file being fixed
  - For modules: `maintainability/<module-name>` (e.g., `maintainability/ec2_instance`)
  - For module_utils: `maintainability/<util-name>` (e.g., `maintainability/botocore`)
  - For other files: `maintainability/<component-name>`
- Base the branch off origin/main

**Step 6.2: Apply Fixes**
- Use the Edit tool to apply each fix
- Add comments where helpful to explain maintainability-related changes
- Ensure fixes follow project coding standards

**Step 6.3: Run Pre-commit Checks**
- Use the `precommit` skill to run format, lint, and unit tests
- If checks fail, analyse failures:
  - If formatting issues, let formatter fix them
  - If test failures, investigate and fix
  - If issues can't be auto-resolved, report to user

**Step 6.4: Commit Changes**
- Create a descriptive commit message focused on the file being fixed:
  ```
  Fix maintainability issues in <file-basename>

  - <line>: <brief description of fix>
  - <line>: <brief description of fix>

  Addresses <count> maintainability issue(s) identified by SonarCloud:
  - <ruleKey>: <rule description>
  - <ruleKey>: <rule description>

  SonarCloud issue keys: <key1>, <key2>, ...
  ```
- Commit with project standards (GPG signing will be handled by user if needed)

**Step 6.5: Create Changelog Fragment**
- Use the `changelog` skill to create a fragment
- Suggested type: `trivial` (maintainability fixes don't change functionality)
- Description: "Fix maintainability issues in <file-basename> identified by SonarCloud"

### 7. Create Pull Request (Optional)

Ask user if they want to create a PR now or continue with more files:
- If create PR now:
  - Use the `create-pr` skill to create a draft PR
  - PR title: "Fix maintainability issues in <file-basename>"
  - PR body should include:
    - File(s) modified
    - List of issues addressed with line numbers and rule keys
    - Description of fixes applied
    - Links to SonarCloud rule documentation
    - Note that SonarCloud will re-analyse after merge
- If continue:
  - Return to step 3 to select another file
  - Each file should typically get its own PR for easier review

### 8. Close Issues (Automatic)

**Note**: SonarCloud issues are automatically closed when:
1. The code fix is merged and SonarCloud re-analyses the project
2. The issue is no longer detected in the updated code

For false positives or won't fix issues, user can:
- Go to SonarCloud UI: https://sonarcloud.io/project/issues?id=ansible-collections_amazon.aws&types=CODE_SMELL
- Find the issue by key or file/line
- Mark as "Won't Fix" or "False Positive" with a comment explaining why

## Important Notes

### API Limitations
- Maximum page size is 500 issues per request
- Use pagination parameters (`p` and `ps`) for larger result sets
- No authentication required for public projects (read-only)
- Issue resolution can only be changed via authenticated API calls or web UI

### Fix Strategies by Common Rule Types

**python:S3776** (Cognitive complexity too high):
- Refactor complex functions into smaller units
- **Prioritise extracting logic that can be cleanly unit-tested**
- Look for self-contained chunks of logic that can be broken out
- Extract nested logic into helper functions
- Simplify conditional statements
- Consider whether extracted functions can be tested without mocking the module or client

**python:S1192** (String literals should not be duplicated):
- Extract duplicated strings into named constants
- Consider if strings represent configuration that should be centralised
- Group related constants together
- Use descriptive names that explain the purpose

**python:S1066** (Collapsible if statements):
- Merge nested if statements where appropriate
- Use boolean operators to simplify logic
- Ensure readability isn't sacrificed

**python:S1541** (Cognitive complexity of functions should not be too high):
- Similar to S3776
- Break down into smaller, focused functions
- Each function should have a single responsibility

**python:S101** (Type names should comply with naming convention):
- Ensure class names use PascalCase
- Ensure other type names follow Python conventions
- May be false positive for Ansible-specific patterns

**python:S1135** (TODO/FIXME tags):
- Implement the TODO if straightforward
- Create issues for complex TODOs
- Remove obsolete TODOs

**python:S125** (Commented-out code):
- Remove if no longer needed
- Convert to documentation if explaining removed functionality
- Uncomment and fix if still relevant

**python:S1186** (Functions should not be empty):
- Implement the function if needed
- Add `pass` with a comment explaining why it's empty
- Remove if truly unused

**Code duplication issues**:
- Extract duplicated code into helper functions
- Consider creating utility modules for common patterns
- Ensure shared code is properly tested

**Documentation issues**:
- Add missing docstrings
- Update outdated documentation
- Ensure public APIs are documented

### Testing Requirements
- All maintainability fixes MUST pass precommit checks
- Pay special attention to unit tests that might rely on specific behaviour
- Consider adding tests for refactored code to prevent regression
- Integration tests may be needed for some fixes

### Review Considerations
- Maintainability fixes should be reviewed carefully by maintainers
- Each PR should be focused on one type of issue or severity level
- Include rationale for why each fix improves code quality
- Document any issues that are false positives or won't fix
- Link to SonarCloud rule documentation
- Ensure refactorings don't introduce new bugs

## Example Usage

User: "Run the maintainability-fixes skill"

Skill:
1. Fetches 234 total issues, 73 unresolved
2. Groups by file, sorted by issue count
3. Shows summary table with file names and issue counts
4. User selects "plugins/modules/ec2_instance.py" (12 issues)
5. Analyses all 12 issues in that file
6. Identifies 2 cognitive complexity issues, 8 string duplication issues, 2 commented code issues
7. Suggests refactoring complex functions and extracting string constants
8. User approves fixes
9. Creates branch `maintainability/ec2_instance`
10. Applies all fixes to the single file, runs tests, commits
11. Creates changelog fragment
12. Asks about PR creation
13. User says "create PR"
14. Creates draft PR titled "Fix maintainability issues in ec2_instance.py"
15. Returns to file selection for remaining files

## API Query Examples

### Basic query - all unresolved maintainability issues:
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&ps=500"
```

### Filter by component (file):
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&componentKeys=ansible-collections_amazon.aws:plugins/modules/ec2_instance.py&ps=500"
```

### Filter by severity:
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&severities=CRITICAL,MAJOR&ps=500"
```

### Filter by rule:
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&rules=python:S3776&ps=500"
```

### Combined filters (specific file and severity):
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&componentKeys=ansible-collections_amazon.aws:plugins/modules/ec2_instance.py&severities=CRITICAL,MAJOR&ps=500"
```

**Note**: The `componentKeys` parameter uses the format `projectKey:filepath`, where filepath is relative to the project root.

## Future Enhancements

- Support for authenticated API calls to mark issues as won't fix
- Integration with GitHub to auto-link PR to SonarCloud analysis
- Automatic detection of false positives based on context
- Support for custom fix patterns per rule type
- Interactive filtering mode with dynamic query building
- Automatic extraction of refactorable code blocks
- Batch processing mode for fixing similar issues across multiple files
