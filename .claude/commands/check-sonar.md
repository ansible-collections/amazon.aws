---
name: check-sonar
description: Fetch and analyze SonarCloud issues for the current pull request
disable-model-invocation: true
---

# Review SonarCloud Issues

Fetch and analyze SonarCloud issues for the current pull request (or a specific PR if provided as argument).

**Steps:**

1. **Get PR number**:
   - If `$1` is provided, use it as the PR number
   - Otherwise, auto-detect from current branch:
     ```bash
     BRANCH=$(git rev-parse --abbrev-ref HEAD)
     gh pr list --repo ansible-collections/amazon.aws --head "$BRANCH" --json number -q '.[0].number'
     ```
   - If no PR found, inform the user and stop

2. **Fetch SonarCloud issues**:
   - Use WebFetch to retrieve issues from SonarCloud API:
     - URL: `https://sonarcloud.io/api/issues/search?componentKeys=ansible-collections_amazon.aws&pullRequest=<pr-number>&ps=500`
   - Parse the JSON response to extract all issues

3. **Categorize issues**:
   - Group by severity: BLOCKER, CRITICAL, MAJOR, MINOR, INFO
   - Group by type: BUG, VULNERABILITY, CODE_SMELL, SECURITY_HOTSPOT
   - Sort by severity (most critical first)

4. **Analyze each issue**:
   - For each issue, provide:
     - **Location**: File path and line number
     - **Rule**: The SonarCloud rule that was violated
     - **Message**: The issue description
     - **Severity**: How critical it is
     - **Type**: Bug, security, code smell, etc.
     - **Actionable fix**: Specific guidance on how to fix it

5. **Provide summary**:
   - Total number of issues
   - Breakdown by severity and type
   - Most critical issues that need immediate attention
   - Link to full SonarCloud analysis:
     `https://sonarcloud.io/project/pull_requests?id=ansible-collections_amazon.aws&pullRequest=<pr-number>`

6. **Offer to fix issues**:
   - Ask if the user wants you to fix any of the issues
   - Prioritize blockers and critical issues first

**Important**: Focus on actionable analysis. For each issue, explain why it's a problem and how to fix it, not just what the rule says.
