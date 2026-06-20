---
name: new-branch
description: Create a new feature branch following project conventions
---

# Create New Feature Branch

Create a new feature branch based on origin/main following project conventions.

## Workflow

### 1. Verify Current State

Check if there are uncommitted changes that should be committed or stashed:
```bash
git status
```

If there are uncommitted changes, ask the user whether to:
- Commit them first
- Stash them
- Discard them
- Continue anyway

### 2. Fetch Latest from Origin

Update the remote tracking branches:
```bash
git fetch origin
```

### 3. Determine Branch Name

Ask the user for the branch name, suggesting patterns based on context:
- `issue/<number>` - For issue-specific work (e.g., `issue/12345`)
- `deprecation/<name>` - For deprecation removal (e.g., `deprecation/utcnow`)
- `<module>/<feature>` - For module enhancements (e.g., `s3_bucket/new_parameter`)
- `sonarcloud/<category>` - For SonarCloud fixes (e.g., `sonarcloud/security`)
- `security/<category>` - For security fixes (e.g., `security/weak-cryptography`)
- `reliability/<category>` - For reliability fixes (e.g., `reliability/duplicate-branches`)
- `maintainability/<module>` - For maintainability fixes (e.g., `maintainability/ec2_instance`)
- `requirements/<desc>` - For dependency updates (e.g., `requirements/python39-boto138`)
- `feature/<name>` - For new features
- `bugfix/<name>` - For bug fixes

Keep branch names short and descriptive.

### 4. Create and Checkout New Branch

Create the branch based on origin/main:
```bash
git checkout -b <branch-name> origin/main
```

### 5. Unset Remote Tracking

After creating a new local branch from origin/main, unset the remote tracking because the branch will be pushed to the user's fork (not origin):
```bash
git branch --unset-upstream
```

### 6. Confirm Success

Display:
- New branch name
- Base commit (from origin/main)
- Reminder that first push should use `-u` flag to set upstream tracking

## Notes

- Always base new branches off `origin/main` to ensure they start from the latest upstream state
- The upstream is unset because new branches will be pushed to a fork remote (not origin)
- First push to remote should use `-u` flag to set tracking
- The default push remote should follow project or user CLAUDE.md configuration
