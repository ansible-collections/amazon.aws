# Security Fixes Workflow

Fetch security hotspots from SonarCloud, analyze them, suggest fixes, and implement approved fixes grouped by security category.

## Overview

This skill pulls security hotspots from the SonarCloud API for the ansible-collections/amazon.aws project, groups them by security category, analyzes the code, suggests fixes, and creates focused PRs for review.

## Workflow

### 1. Fetch Security Hotspots

Retrieve unreviewed security hotspots from SonarCloud:

```bash
curl -s "https://sonarcloud.io/api/hotspots/search?projectKey=ansible-collections_amazon.aws&status=TO_REVIEW&ps=500"
```

Parse the JSON response to extract:
- Total count of hotspots
- List of hotspots with: key, component (file path), securityCategory, vulnerabilityProbability, line, message, ruleKey
- Component details

### 2. Group by Security Category

Group the hotspots by `securityCategory` field. Common categories include:
- `weak-cryptography` - Cryptographic issues
- `encrypt-data` - Data encryption issues (e.g., HTTP vs HTTPS)
- `dos` - Denial of Service vulnerabilities
- `permission` - Permission and access control issues
- `injection` - Injection vulnerabilities
- `auth` - Authentication issues
- `insecure-conf` - Insecure configuration

For each category, create a summary showing:
- Category name and description
- Number of hotspots
- Severity distribution (HIGH/MEDIUM/LOW)
- Affected files
- Rule types involved

### 3. Present Categories to User

Display a summary table of all categories with hotspots:

```
Security Hotspots Summary (TO_REVIEW only)
===========================================

Category           | Count | Severity       | Files Affected
-------------------|-------|----------------|---------------
weak-cryptography  |   2   | MEDIUM (2)     | aws_ssm.py, terminalmanager.py
encrypt-data       |   5   | LOW (5)        | transformations.py, ec2_metadata_facts.py
dos               |   1   | MEDIUM (1)     | ec2_security_group.py
```

Ask the user which category they want to address first.

### 4. Analyze and Suggest Fixes

For the selected category:

**Step 4.1: Read Affected Files**
- Use the Read tool to read each affected file
- Focus on the specific line numbers mentioned in the hotspots

**Step 4.2: Analyze Each Hotspot**
For each hotspot in the category:
- Display the issue details:
  - File and line number
  - SonarCloud message
  - Rule key and link to rule documentation
  - Code snippet showing the problematic line(s)
- Analyze the context:
  - Read surrounding code to understand intent
  - Check if this is a false positive
  - Consider project patterns and standards
- Suggest a fix:
  - Provide specific code changes
  - Explain why this fix is appropriate
  - Note any potential side effects
  - Consider if this is actually safe to ignore (mark as SAFE) vs needs fixing

**Step 4.3: Group Fixes by Approach**
Group suggested fixes into logical units:
- If multiple issues in the same file can be fixed together, group them
- If issues require the same type of change, group them
- Keep groups small enough to be reviewable (prefer multiple small PRs over one large PR)

### 5. Get User Approval

Present all suggested fixes for the category and ask:
- Which fixes should be implemented?
- Which fixes should be marked as false positives/safe to ignore?
- Which fixes need more investigation?

Use AskUserQuestion to let the user select:
- "Implement all suggested fixes"
- "Implement selected fixes" (then ask which ones)
- "Skip this category"
- "Mark as safe" (for false positives)

### 6. Implement Approved Fixes

For each approved fix:

**Step 6.1: Create Feature Branch**
- Check current branch (should be on main)
- Create a descriptive branch name: `security/<category>` (e.g., `security/weak-cryptography`)
- Base the branch off origin/main

**Step 6.2: Apply Fixes**
- Use the Edit tool to apply each fix
- Add comments where helpful to explain security-related changes
- Ensure fixes follow project coding standards

**Step 6.3: Run Pre-commit Checks**
- Use the `precommit` skill to run format, lint, and unit tests
- If checks fail, analyze failures:
  - If formatting issues, let formatter fix them
  - If test failures, investigate and fix
  - If issues can't be auto-resolved, report to user

**Step 6.4: Commit Changes**
- Create a descriptive commit message:
  ```
  Fix <category> security hotspots

  - <file1>:<line> - <brief description of fix>
  - <file2>:<line> - <brief description of fix>

  Addresses <count> security hotspot(s) identified by SonarCloud:
  - <ruleKey>: <rule description>

  SonarCloud hotspot keys: <key1>, <key2>, ...
  ```
- Commit with project standards (GPG signing will be handled by user if needed)

**Step 6.5: Create Changelog Fragment**
- Use the `changelog` skill to create a fragment
- Suggested type: `trivial` (security fixes don't change functionality)
- Description: "Fix <category> security hotspots identified by SonarCloud"

### 7. Create Pull Request (Optional)

Ask user if they want to create a PR now or continue with more categories:
- If create PR now:
  - Use the `create-pr` skill to create a draft PR
  - PR title: "Fix <category> security hotspots"
  - PR body should include:
    - List of hotspots addressed
    - Links to SonarCloud hotspot details
    - Description of fixes applied
    - Note that SonarCloud will re-analyze after merge
- If continue:
  - Return to step 3 to select another category
  - User can create a combined PR for multiple categories later

### 8. Mark Hotspots as Reviewed (Manual Step)

**Note**: SonarCloud hotspots can only be marked as reviewed through the web UI or by specific API calls that require authentication. After implementing fixes:

1. The fixes will be detected by SonarCloud on the next analysis
2. If fixed, the hotspot will automatically resolve
3. If marking as false positive, user should:
   - Go to SonarCloud UI: https://sonarcloud.io/project/security_hotspots?id=ansible-collections_amazon.aws
   - Find the hotspot by key or file/line
   - Mark as "SAFE" or "ACKNOWLEDGED" with a comment explaining why

## Important Notes

### API Limitations
- Maximum page size is 500 hotspots
- No authentication required for public projects (read-only)
- Hotspot status can only be changed via authenticated API calls or web UI

### Fix Strategies by Category

**weak-cryptography**:
- Often involves `random` module usage
- Consider if cryptographic randomness is actually needed
- If yes, use `secrets` module instead
- If no (e.g., unique IDs), mark as SAFE with comment

**encrypt-data**:
- Usually HTTP vs HTTPS issues
- Check if HTTP is required (e.g., AWS metadata endpoint at http://169.254.169.254)
- If required, mark as SAFE with comment explaining why
- Otherwise, change to HTTPS

**dos**:
- Often regex backtracking issues
- Analyze if input is user-controlled
- Simplify regex or add input validation
- May require significant refactoring

**permission**:
- Access control and privilege issues
- May involve GitHub Actions permissions
- Analyze security implications carefully
- Some may be false positives in trusted environments

### Testing Requirements
- All security fixes MUST pass precommit checks
- Pay special attention to unit tests that might rely on specific behavior
- Consider adding tests for security-sensitive code paths
- Integration tests may be needed for some fixes

### Review Considerations
- Security fixes should be reviewed carefully by maintainers
- Each PR should be focused on one security category
- Include rationale for why each fix is safe
- Document any hotspots that are false positives
- Link to SonarCloud rule documentation

## Example Usage

User: "Run the security-fixes skill"

Skill:
1. Fetches 43 total hotspots, 8 TO_REVIEW
2. Groups into 3 categories
3. Shows summary table
4. User selects "weak-cryptography"
5. Analyzes 2 hotspots in aws_ssm.py and terminalmanager.py
6. Suggests using `secrets.token_hex()` instead of `random`
7. User approves fixes
8. Creates branch `security/weak-cryptography`
9. Applies fixes, runs tests, commits
10. Creates changelog fragment
11. Asks about PR creation
12. User says "create PR"
13. Creates draft PR with details
14. Returns to category selection for remaining hotspots

## Future Enhancements

- Support for authenticated API calls to mark hotspots as reviewed
- Integration with GitHub to auto-link PR to SonarCloud analysis
- Support for fixing REVIEWED hotspots that were marked incorrectly
- Automatic detection of false positives based on context
- Support for custom fix patterns per rule type
