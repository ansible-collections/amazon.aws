---
description: Check GitHub Actions status and suggest fixes for failures
---

Check the status of GitHub Actions for the current branch and analyze any failures.

For the current branch:
1. Get the PR number associated with this branch from the upstream repository (ansible-collections/amazon.aws)
   - Use: `gh pr list --repo ansible-collections/amazon.aws --head ssm/connection_refactor`
   - If no PR exists, check for recent workflow runs on the branch directly
2. List recent workflow runs to identify failures
   - Always use `--repo ansible-collections/amazon.aws` flag
   - Use the branch name to filter: `gh run list --repo ansible-collections/amazon.aws --branch BRANCH_NAME`
3. For failed jobs, focus on matrix tests (sanity/unit):
   - Identify the oldest Python/Ansible combination that failed
   - Identify the latest Python/Ansible combination that failed
   - Fetch and analyze logs from both to understand the failure pattern
4. Summarize the failures clearly:
   - What tests are failing
   - Which Python/Ansible combinations are affected
   - The actual error messages from the logs
5. Suggest specific fixes based on the error patterns
6. If the fix is straightforward (like formatting, linting, or sanity issues), offer to apply it

Important:
- PRs are on ansible-collections/amazon.aws (upstream), not personal forks
- Always include `--repo ansible-collections/amazon.aws` in all gh commands
- Only examine the oldest and newest failing combinations in matrix tests
- Skip passed tests entirely
- Focus on actionable errors, not warnings
- Provide concrete file paths and line numbers when available
