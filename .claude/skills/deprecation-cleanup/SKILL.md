# Deprecation Cleanup Workflow

Find and remediate overdue deprecation warnings in the codebase. This skill helps identify deprecated code that should have been removed or changed based on the deprecation date or version.

## Overview

This skill searches for deprecation warnings throughout the codebase, identifies those that are overdue (past their removal date or version), and helps implement the necessary changes to remove the deprecated functionality. It handles both date-based deprecations (e.g., `date="2024-12-01"`) and version-based deprecations (e.g., `version="12.0.0"`).

## Workflow

### 1. Find All Deprecation Warnings

Search for deprecation calls in the codebase:

```bash
# Find deprecate() calls in plugins
grep -rn "\.deprecate(" plugins/ --include="*.py"
```

For each deprecation found, extract:
- File and line number
- Date parameter (e.g., `date="2024-12-01"`)
- Version parameter (e.g., `version="8.0.0"`)
- Deprecation message
- Context - what code is being deprecated

### 2. Determine Current and Next Versions

Use the next-version skill logic to determine version context:

```bash
# Find current major version from stable branches
MAJOR=$(git branch -r | grep -o 'stable-[0-9]\+' | grep -o '[0-9]\+' | sort -n | tail -1)

# Find latest release tag
CURRENT_VERSION=$(git tag --list --sort=-version:refname | grep "^${MAJOR}\." | head -1)

# Calculate next versions (minor: X.(Y+1).0, major: (X+1).0.0)
```

### 3. Compare Deprecations Against Current Date and Version

**Today's date:** 2026-03-25

**Date-based deprecations:**
- Parse the `date` parameter
- Compare to today's date
- Identify if overdue (date < today)
- Calculate how many days/months overdue

**Version-based deprecations:**
- Parse the `version` parameter
- Compare to current and next versions:
  - **Overdue**: version <= current version
  - **Blocks next major**: version == next major
  - **Blocks next minor**: version == next minor
  - **Future**: version > next major

### 4. Categorise Deprecations

**Priority order:**
1. **CRITICAL** - Overdue (date or version), should be removed immediately
2. **HIGH** - Blocks next major release
3. **MEDIUM** - Blocks next minor release OR upcoming date-based (0-3 months)
4. **LOW** - Future deprecations (>3 months or version > next major)

**Type categories:**
- Parameter deprecations
- Mode/option deprecations
- Module deprecations
- Functionality deprecations
- Behaviour changes

### 5. Present Summary to User

Display a summary table with version context:

```
Current Version: 11.2.0
Next Minor: 11.3.0
Next Major: 12.0.0

Deprecation Status Summary
==========================

Total deprecations found: X

By Priority:
  CRITICAL (overdue - action required now): Y
  HIGH (blocks next major 12.0.0): A
  MEDIUM (blocks next minor 11.3.0 or upcoming): B
  LOW (future): C

CRITICAL - Overdue Deprecations
================================

File                          | Line | Overdue By        | Type      | Description
------------------------------|------|-------------------|-----------|------------------
plugins/modules/s3_object.py  | 1375 | 115 days          | Parameter | dualstack + endpoint_url
```

For each deprecation, show:
- Full context (file, line, code snippet)
- What needs to be removed/changed
- Suggested implementation approach
- Potential breaking change impact
- For version-based: which release it blocks

### 6. Get User Selection

Ask the user which deprecation(s) to address:

- "Fix all CRITICAL (overdue) deprecations"
- "Fix all HIGH (blocks major) deprecations"
- "Fix all MEDIUM (blocks minor) deprecations"
- "Fix selected deprecation"
- "Show details for specific deprecation"

### 7. Implement Deprecation Removal

Follow the appropriate pattern based on deprecation type:

**Pattern A: Remove Deprecated Parameter/Choice**
1. Read module documentation (DOCUMENTATION block)
2. Remove from: DOCUMENTATION, argument_spec, validation logic
3. Remove deprecation warning
4. Remove usages in tests/examples

**Pattern B: Remove Deprecated Mode/Behaviour**
1. Remove mode from valid choices
2. Remove all code paths handling that mode
3. Remove deprecation warning
4. Update documentation
5. Remove integration tests for that mode

**Pattern C: Change Default Behaviour**
1. Remove old behaviour code path
2. Remove compatibility shim
3. Remove deprecation warning
4. Update parameter default value
5. Update documentation

**Pattern D: Remove Entire Deprecated Feature**
1. Remove all code related to the feature
2. Remove deprecation warning
3. Remove documentation
4. Remove integration tests
5. Update CHANGELOG to document breaking change

### 8. Run Tests

**Run pre-commit checks:**
- Use `precommit` skill (format, lint, unit tests)
- Fix any failures

**Run integration tests (if applicable):**
- If deprecation affected module behaviour, use `integration-tests` skill
- Verify tests pass or update appropriately

**Check for remaining references:**
- Search codebase for references to removed functionality
- Check examples, documentation, tests
- Update or remove as needed

### 9. Create Changelog Fragment

Use the `changelog` skill to create a breaking change fragment:

```yaml
breaking_changes:
  - >-
    module_name - removed support for deprecated_feature.
    The deprecated_feature was deprecated in version X.Y.Z and the deprecation
    period has now ended (https://github.com/ansible-collections/amazon.aws/pull/XXXX).
```

Or for minor breaking changes:
```yaml
minor_changes:
  - >-
    module_name - removed deprecated parameter old_param.
    Use new_param instead (https://github.com/ansible-collections/amazon.aws/pull/XXXX).
```

### 10. Commit and Create PR

**Commit message format:**

For date-based:
```
Remove overdue deprecation in module_name

- Remove support for deprecated_feature (deprecated since X.Y.Z, removal date YYYY-MM-DD)
- Update documentation and tests

The deprecation period ended on YYYY-MM-DD. Users should migrate to new_feature.
```

For version-based:
```
Remove deprecation scheduled for X.Y.Z in module_name

- Remove support for deprecated_feature (deprecated in A.B.C, removal in X.Y.Z)
- Update documentation and tests

This removal was scheduled for version X.Y.Z. Users should migrate to new_feature.
```

**Create PR:**
- Use `create-pr` skill
- Title: "Remove overdue deprecation: [description]"
- Include: what was deprecated, when, why removing now, migration guide
- Label as `breaking-change`

## Important Notes

### Breaking Changes
- Deprecation removals are **breaking changes**
- Always use `breaking_changes` section in changelog for major removals
- Consider creating a migration guide if widely used
- Add `breaking-change` label to PRs

### Version-based Deprecations for Major Releases
- Deprecations marked with `version="12.0.0"` must be removed BEFORE releasing 12.0.0
- Create dedicated branch/PR for all major-blocking deprecations
- Review and batch all `version="12.0.0"` deprecations together

### Edge Cases

**Deprecations in module_utils:**
- May affect multiple modules
- Check all modules that import the utility: `grep -r "from.*module_utils.*import.*deprecated_function"`
- More complex impact analysis required

**Deprecations with both date AND version:**
- Use whichever comes first as the removal trigger
- Example: `date="2024-12-01", version="12.0.0"` - if date is overdue, it's overdue

## Example Usage

**Preparing for 12.0.0 major release:**

1. Determines current: 11.2.0, next major: 12.0.0
2. Searches for all deprecations
3. Finds 5 deprecations marked `version="12.0.0"` (HIGH priority - blocks major)
4. User selects "Fix all HIGH (blocks major) deprecations"
5. Processes all 5 deprecations
6. Creates changelog fragments (all as breaking_changes)
7. Runs full prepush checks
8. Creates PR: "Remove all deprecations scheduled for 12.0.0"
9. PR tagged with `breaking-change` and labels
10. Once merged, version 12.0.0 can be released
