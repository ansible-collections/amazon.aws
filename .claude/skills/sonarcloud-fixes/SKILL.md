# SonarCloud Fixes Workflow

Fetch issues from SonarCloud, analyse them, suggest fixes, and implement approved fixes.

## Overview

This skill pulls issues from the SonarCloud API for the ansible-collections/amazon.aws project, groups them appropriately, analyses the code, suggests fixes, and creates focused PRs for review.

Supports three issue types:
- **Security hotspots** - Security vulnerabilities and potential security issues
- **Reliability issues** - Bugs and potential runtime errors
- **Maintainability issues** - Code smells and technical debt

## Workflow

### 1. Determine Issue Type

Ask the user which type of issues to address (unless context makes it clear):
- Security hotspots (vulnerabilities, weak cryptography, etc.)
- Reliability issues (bugs, logic errors, exceptions)
- Maintainability issues (code smells, complexity, duplication)

Or auto-detect from context (e.g., if invoked via `/fix-sonarcloud-security` command).

### 2. Fetch Issues from SonarCloud

Retrieve unresolved issues from SonarCloud using the appropriate API:

**For Security Hotspots:**
```bash
curl -s "https://sonarcloud.io/api/hotspots/search?projectKey=ansible-collections_amazon.aws&status=TO_REVIEW&ps=500"
```

**For Reliability Issues:**
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=BUG&resolved=false&ps=500"
```

**For Maintainability Issues:**
```bash
curl -s "https://sonarcloud.io/api/issues/search?projectKey=ansible-collections_amazon.aws&types=CODE_SMELL&resolved=false&ps=500"
```

Parse the JSON response to extract issue details: key, component (file path), severity/category, line number, message, rule.

### 3. Group Issues

Group issues using the strategy appropriate for the issue type:

**Security Hotspots:** Group by `securityCategory`:
- `weak-cryptography` - Cryptographic issues (often `random` module usage)
- `encrypt-data` - Data encryption issues (HTTP vs HTTPS)
- `dos` - Denial of Service vulnerabilities (regex backtracking)
- `permission` - Permission and access control issues
- `injection` - Injection vulnerabilities
- `auth` - Authentication issues
- `insecure-conf` - Insecure configuration

**Reliability Issues:** Group by `severity`:
- `BLOCKER` - Must be fixed immediately
- `CRITICAL` - Critical bugs
- `MAJOR` - Major bugs
- `MINOR` - Minor bugs
- `INFO` - Informational

**Maintainability Issues:** Group by `component` (file path), then by severity within each file. This allows fixing all issues in a file together.

### 4. Present Summary to User

Display a summary table appropriate for the issue type:

**Security Example:**
```
Security Hotspots Summary (TO_REVIEW only)
===========================================

Category           | Count | Severity       | Files Affected
-------------------|-------|----------------|---------------
weak-cryptography  |   2   | MEDIUM (2)     | aws_ssm.py, terminalmanager.py
encrypt-data       |   5   | LOW (5)        | transformations.py, ec2_metadata_facts.py
```

**Reliability Example:**
```
Reliability Issues Summary (Unresolved only)
============================================

Severity    | Count | Common Rules                      | Files Affected
------------|-------|-----------------------------------|---------------
CRITICAL    |   2   | python:S1862, python:S3776        | module1.py, module2.py
MAJOR       |   15  | python:S112, python:S1135         | various
```

**Maintainability Example:**
```
Maintainability Issues Summary (Unresolved only)
=================================================

File                                    | Total | CRIT | MAJOR | MINOR | Common Rules
----------------------------------------|-------|------|-------|-------|------------------
plugins/modules/ec2_instance.py         |   12  |   2  |   8   |   2   | S3776, S1192
plugins/module_utils/botocore.py        |   8   |   1  |   5   |   2   | S1066, S1192
```

Ask the user which group to address first.

### 5. Analyse and Suggest Fixes

For the selected group:

**a) Read affected files** using the Read tool, focusing on specific line numbers.

**b) Analyse each issue:**
- Display issue details (file, line, message, rule documentation link)
- Read surrounding code to understand context
- Check for false positives
- Consider project patterns and standards

**c) Suggest fixes:**
- Provide specific code changes
- Explain rationale
- Note potential side effects
- Identify false positives that should be marked as SAFE/won't fix

**d) Group fixes logically:**
- Multiple issues in the same file can be fixed together
- Issues requiring the same type of change can be grouped
- Keep groups reviewable (prefer multiple small PRs)

### 6. Get User Approval

Present all suggested fixes and ask which to implement:
- "Implement all suggested fixes"
- "Implement selected fixes" (then ask which ones)
- "Skip this group"
- "Mark as safe/won't fix" (for false positives)

### 7. Implement Approved Fixes

**a) Create feature branch:**
- Use the `new-branch` skill to create a new feature branch
- Suggested branch naming based on issue type:
  - Security: `security/<category>` (e.g., `security/weak-cryptography`)
  - Reliability: `reliability/<rule-or-category>` (e.g., `reliability/duplicate-branches`)
  - Maintainability: `maintainability/<module-name>` (e.g., `maintainability/ec2_instance`)

**b) Apply fixes:**
- Use Edit tool to apply each fix
- Add explanatory comments where helpful
- Follow project coding standards

**c) Run pre-commit checks:**
- Use `precommit` skill (format, lint, unit tests)
- Analyse and fix any failures
- Report issues that can't be auto-resolved

**d) Commit changes:**
```
Fix <type> <category/severity> issues

- <file>:<line> - <brief description>
- <file>:<line> - <brief description>

Addresses <count> <type> issue(s) identified by SonarCloud:
- <ruleKey>: <rule description>

SonarCloud issue keys: <key1>, <key2>...
```

**e) Create changelog fragment:**
- Use `changelog` skill
- Type based on issue category:
  - Security hotspots: `trivial` (or `security_fixes` if actual vulnerability)
  - Reliability issues: `bugfixes`
  - Maintainability issues: `trivial`
- Description: "Fix <type> issues identified by SonarCloud"

### 8. Create Pull Request (Optional)

Ask if user wants to create PR now or continue with more issues:
- If create PR: Use `create-pr` skill
- PR title: "Fix <type> <category/severity> issues"
- Include links to SonarCloud issue details
- If continue: Return to step 4 for next group

### 9. Mark Issues as Reviewed (Manual)

SonarCloud issues resolve automatically when fixes are merged and re-analysed.

For false positives, user should manually mark in SonarCloud UI:
- Security: https://sonarcloud.io/project/security_hotspots?id=ansible-collections_amazon.aws
- Reliability/Maintainability: https://sonarcloud.io/project/issues?id=ansible-collections_amazon.aws

## Fix Strategies by Common Patterns

**Weak Cryptography (python:S2245):**
- Check if cryptographic randomness is actually needed
- If yes: use `secrets` module instead of `random`
- If no (e.g., unique IDs): mark as SAFE with explanation

**HTTP vs HTTPS (encrypt-data):**
- Check if HTTP is required (e.g., AWS metadata at http://169.254.169.254)
- If required: mark as SAFE with explanation
- Otherwise: change to HTTPS

**Cognitive Complexity (python:S3776):**
- Refactor complex functions into smaller units
- **Prioritise extracting logic that can be cleanly unit-tested**
- Extract nested logic into helper functions
- Simplify conditional statements

**Duplicate Strings (python:S1192):**
- Extract duplicated strings into named constants
- Group related constants together
- Use descriptive names

**Duplicate Branch (python:S1862):**
- Refactor conditional logic to remove duplicates
- Check if different conditions should have different logic

**Generic Exceptions (python:S112):**
- Replace with specific exception types
- Consider custom exception classes where appropriate

**TODO/FIXME Tags (python:S1135):**
- Implement if straightforward
- Create issues for complex TODOs
- Remove obsolete TODOs

**Commented Code (python:S125):**
- Remove if no longer needed
- Convert to documentation if explaining removed functionality

## Important Notes

### Testing Requirements
- All fixes MUST pass precommit checks
- Pay attention to unit tests that might rely on specific behaviour
- Consider adding tests for fixed code paths
- Integration tests may be needed for some fixes

### Review Considerations
- Each PR should be focused on one type/category
- Include rationale for why each fix is safe
- Document false positives
- Link to SonarCloud rule documentation
- For maintainability: ensure refactorings don't introduce bugs

### API Limitations
- Maximum page size: 500 issues/hotspots
- No authentication required for public projects (read-only)
- Issue resolution only via authenticated API or web UI

## Example Usage

User invokes `/fix-sonarcloud-security`

1. Auto-detects security issue type
2. Fetches 8 TO_REVIEW hotspots
3. Groups into 3 categories (weak-cryptography, encrypt-data, dos)
4. Shows summary table
5. User selects "weak-cryptography"
6. Analyses 2 hotspots (random module usage)
7. Suggests using `secrets.token_hex()` instead
8. User approves
9. Creates branch `security/weak-cryptography`
10. Applies fixes, runs tests, commits
11. Creates changelog fragment
12. Creates draft PR
13. Returns to category selection for remaining hotspots
