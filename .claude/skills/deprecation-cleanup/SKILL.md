# Deprecation Cleanup Workflow

Find and remediate overdue deprecation warnings in the codebase. This skill helps identify deprecated code that should have been removed or changed based on the deprecation date or version.

## Overview

This skill searches for deprecation warnings throughout the codebase, identifies those that are overdue (past their removal date or version), and helps implement the necessary changes to remove the deprecated functionality. It handles both date-based deprecations (e.g., `date="2024-12-01"`) and version-based deprecations (e.g., `version="12.0.0"`).

## Workflow

### 1. Find All Deprecation Warnings

Search for deprecation calls in the codebase:

```bash
# Find module.deprecate() calls in Python modules
grep -rn "module\.deprecate(" plugins/ --include="*.py"

# Find deprecate() calls in module_utils
grep -rn "\.deprecate(" plugins/module_utils/ --include="*.py"

# Find deprecate() calls in plugins (inventory, lookup, etc.)
grep -rn "\.deprecate(" plugins/inventory/ plugins/lookup/ plugins/connection/ --include="*.py"
```

### 2. Parse Deprecation Information

For each deprecation found, extract:
- **File and line number** where the deprecation is defined
- **Date parameter** (e.g., `date="2024-12-01"`)
- **Version parameter** (e.g., `version="8.0.0"`) if used instead of date
- **Collection name** (usually `collection_name="amazon.aws"`)
- **Deprecation message** explaining what's deprecated and what should be used instead
- **Context** - what code is being deprecated

Example deprecation pattern:
```python
module.deprecate(
    (
        "Support for 'list' mode has been deprecated and will be removed in a release after "
        "2026-11-01.  Please use the amazon.aws.s3_object_info module instead."
    ),
    date="2026-11-01",
    collection_name="amazon.aws",
)
```

### 3. Determine Current and Next Versions

Use the next-version skill logic to determine version context:

```bash
# Find current major version from stable branches
MAJOR=$(git branch -r | grep -o 'stable-[0-9]\+' | grep -o '[0-9]\+' | sort -n | tail -1)

# Find latest release tag
CURRENT_VERSION=$(git tag --list --sort=-version:refname | grep "^${MAJOR}\." | head -1)

# Calculate next versions
# Next minor: X.(Y+1).0
# Next major: (X+1).0.0
```

**Current version context:**
- Stable branch: `stable-11`
- Current version: `11.2.0`
- Next minor: `11.3.0`
- Next major: `12.0.0`

### 4. Compare Deprecations Against Current Date and Version

**Today's date:** 2026-03-25

For each deprecation, check both date and version parameters:

#### Date-based deprecations:
- Parse the `date` parameter (e.g., `date="2024-12-01"`)
- Compare to today's date (2026-03-25)
- Identify if overdue (date < 2026-03-25)
- Calculate how many days/months overdue

#### Version-based deprecations:
- Parse the `version` parameter (e.g., `version="12.0.0"`)
- Compare to current version and next versions:
  - **Overdue**: version <= current version (should have been removed already)
  - **Due for next major**: version == next major (must be removed before next major release)
  - **Due for next minor**: version == next minor (must be removed before next minor release)
  - **Future**: version > next major

Examples:
- `version="11.0.0"` - **OVERDUE** (current is 11.2.0)
- `version="12.0.0"` - **Due for next major** (blocks major release)
- `version="11.3.0"` - **Due for next minor** (blocks minor release)
- `version="13.0.0"` - **Future** (not yet actionable)

### 5. Categorise Deprecations

Group deprecations by priority:

**Date-based categories:**
- **Overdue** - past the removal date, needs immediate action
- **Upcoming** - within next 3 months, plan for removal
- **Future** - more than 3 months away

**Version-based categories:**
- **Overdue** - version <= current version, should already be removed
- **Blocks next major** - version == next major version (e.g., 12.0.0), must remove before major release
- **Blocks next minor** - version == next minor version (e.g., 11.3.0), must remove before minor release
- **Future** - version > next major, not yet actionable

**Combined priority order:**
1. **CRITICAL** - Overdue (date or version), should be removed immediately
2. **HIGH** - Blocks next major release (version-based only)
3. **MEDIUM** - Blocks next minor release OR upcoming date-based (0-3 months)
4. **LOW** - Future deprecations (>3 months or version > next major)

Within each priority level, categorise by type:
- **Parameter deprecations** - deprecated module parameters
- **Mode/option deprecations** - deprecated modes or choices
- **Module deprecations** - entire modules being deprecated
- **Functionality deprecations** - features being removed
- **Behaviour changes** - default behaviour changes

### 6. Present Summary to User

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
plugins/modules/s3_object.py  | 1375 | 115 days          | Parameter | dualstack + endpoint_url (date)
plugins/modules/example.py    | 234  | 1 minor version   | Mode      | deprecated_mode (version 11.0.0)

HIGH - Blocks Next Major (12.0.0)
==================================

File                          | Line | Version | Type      | Description
------------------------------|------|---------|-----------|------------------
plugins/modules/foo.py        | 456  | 12.0.0  | Parameter | old_param removal
plugins/modules/bar.py        | 789  | 12.0.0  | Feature   | legacy_mode removal

MEDIUM - Blocks Next Minor (11.3.0) or Upcoming
================================================

File                          | Line | Version/Date | Type      | Description
------------------------------|------|--------------|-----------|------------------
plugins/modules/baz.py        | 123  | 11.3.0       | Parameter | temp_param removal
plugins/modules/qux.py        | 456  | 2026-05-15   | Behaviour | default value change
```

For each deprecation, show:
- Full context (file, line, code snippet)
- What needs to be removed/changed
- Suggested implementation approach
- Potential breaking change impact
- For version-based: which release it blocks

### 7. Get User Selection

Ask the user which deprecation(s) to address:

Use AskUserQuestion to let the user select:
- "Fix all CRITICAL (overdue) deprecations"
- "Fix all HIGH (blocks major) deprecations" - for preparing major release
- "Fix all MEDIUM (blocks minor) deprecations" - for preparing minor release
- "Fix selected deprecation" (then ask which one)
- "Show details for specific deprecation"

### 8. Implement Deprecation Removal

For each selected deprecation, follow the appropriate pattern:

#### Pattern A: Remove Deprecated Parameter/Choice

If a parameter or choice was deprecated:
1. Read the module documentation (DOCUMENTATION block)
2. Remove the deprecated parameter/choice from:
   - DOCUMENTATION
   - argument_spec
   - Any validation logic
3. Remove the deprecation warning itself
4. Search for usages in:
   - Integration tests
   - Example playbooks
   - Documentation examples

Example:
```python
# BEFORE: Deprecated parameter
argument_spec = dict(
    old_param=dict(type='str'),  # Remove this
    new_param=dict(type='str'),  # Keep this
)
if module.params.get('old_param'):
    module.deprecate(...)  # Remove this warning
    # Handle old_param  # Remove this handling
```

```python
# AFTER: Deprecated parameter removed
argument_spec = dict(
    new_param=dict(type='str'),
)
# old_param handling removed entirely
```

#### Pattern B: Remove Deprecated Mode/Behaviour

If a mode or behaviour was deprecated:
1. Remove the mode from valid choices
2. Remove all code paths that handle that mode
3. Remove the deprecation warning
4. Update documentation to remove references
5. Remove integration tests for that mode

Example:
```python
# BEFORE
mode=dict(choices=['get', 'put', 'list', 'delobj'], required=True)  # 'list' deprecated

if module.params.get('mode') == 'list':
    module.deprecate("...")  # Remove
    do_s3_object_list(...)  # Remove function call

# AFTER
mode=dict(choices=['get', 'put', 'delobj'], required=True)  # 'list' removed
# All 'list' mode handling removed
```

#### Pattern C: Change Default Behaviour

If the deprecation warns about a behaviour change:
1. Remove the old behaviour code path
2. Remove the compatibility shim
3. Remove the deprecation warning
4. Update the parameter default value
5. Update documentation

Example:
```python
# BEFORE: Compatibility for old boolean values
if module.params.get('overwrite') not in ('always', 'never', 'different', 'latest'):
    module.deprecate("...")  # Warns about boolean usage
    if module.boolean(module.params['overwrite']):  # Compatibility shim
        variable_dict['overwrite'] = 'always'
    else:
        variable_dict['overwrite'] = 'never'

# AFTER: Only accept string values
# Removed the if block entirely - no more boolean support
# Only 'always', 'never', 'different', 'latest' accepted
```

#### Pattern D: Remove Entire Deprecated Feature

If an entire feature is deprecated:
1. Remove all code related to the feature
2. Remove the deprecation warning
3. Remove documentation
4. Remove integration tests
5. Update CHANGELOG to document breaking change

### 9. Run Tests

After making changes:

**Step 9.1: Run Pre-commit Checks**
- Use the `precommit` skill to run format, lint, and unit tests
- Fix any failures

**Step 9.2: Run Integration Tests (if applicable)**
- If the deprecation affected module behaviour, run integration tests
- Use the `integration-tests` skill
- Verify tests pass or update tests appropriately

**Step 9.3: Check for Remaining References**
- Search codebase for references to removed functionality
- Check examples, documentation, tests
- Update or remove as needed

### 10. Create Changelog Fragment

Use the `changelog` skill to create a breaking change fragment:

Suggested format:
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

### 11. Commit Changes

Create a commit with a descriptive message:

For date-based deprecations:
```
Remove overdue deprecation in module_name

- Remove support for deprecated_feature (deprecated since X.Y.Z, removal date 2024-12-01)
- Remove deprecated parameter old_param
- Update documentation to remove references
- Update integration tests

The deprecation period ended on YYYY-MM-DD. Users should migrate to new_feature
as documented in the deprecation warning.
```

For version-based deprecations:
```
Remove deprecation scheduled for X.Y.Z in module_name

- Remove support for deprecated_feature (deprecated in version A.B.C, removal in X.Y.Z)
- Remove deprecated parameter old_param
- Update documentation to remove references
- Update integration tests

This removal was scheduled for version X.Y.Z. Users should migrate to new_feature
as documented in the deprecation warning.
```

### 12. Create Pull Request (Optional)

Ask user if they want to create a PR now or continue with more deprecations:
- If create PR now:
  - Use the `create-pr` skill
  - PR title: "Remove overdue deprecation: [description]"
  - PR body should include:
    - What was deprecated and when
    - Why it's being removed now (overdue by X days/months)
    - Migration guide for users still using old functionality
    - Breaking change notice
    - Label as `breaking-change`
- If continue:
  - Return to step 5 to select another deprecation

## Important Notes

### Breaking Changes

- Deprecation removals are **breaking changes**
- Always use `breaking_changes` section in changelog for major removals
- Consider creating a migration guide if the feature was widely used
- Add `breaking-change` label to PRs

### Testing Strategy

- **Unit tests** - ensure removed code paths don't break unit tests
- **Integration tests** - verify behaviour with removed feature
- **Documentation examples** - check all examples still work
- **Sanity tests** - ensure code quality after removal

### Communication

When creating PRs for overdue deprecations:
1. Clearly state the feature was deprecated and when
2. Explain the deprecation period has ended
3. Provide migration guidance for users
4. Reference the original deprecation PR if available
5. Be empathetic - some users may have missed the deprecation

### Edge Cases

**Version-based deprecations for major releases:**
- Deprecations marked with `version="12.0.0"` should be removed BEFORE releasing 12.0.0
- Create a dedicated branch/PR for all major-blocking deprecations
- Review and batch all `version="12.0.0"` deprecations together
- This ensures the major release is clean and breaking changes are documented

**Deprecation in module_utils:**
- May affect multiple modules
- Need to check all modules that import the utility
- Use `grep -r "from.*module_utils.*import.*deprecated_function"` to find all usages
- More complex impact analysis required
- Consider deprecating at the module level first before removing from module_utils

**Deprecation in plugins (inventory, lookup, etc.):**
- Follow same process as modules
- May have different testing requirements
- Some plugins use `display.deprecated()` instead of `module.deprecate()`

**Deprecations with both date AND version:**
- Some deprecations specify both `date` and `version`
- Use whichever comes first as the removal trigger
- Example: `date="2024-12-01", version="12.0.0"` - if date is overdue but version is next major, it's overdue

## Example Usage

### Example 1: Date-based Deprecation Cleanup

User: "Run the deprecation-cleanup skill"

Skill:
1. Determines current version: 11.2.0, next minor: 11.3.0, next major: 12.0.0
2. Searches codebase for all deprecation warnings
3. Finds 18 total deprecations:
   - 3 CRITICAL (overdue by date or version)
   - 5 HIGH (blocks major 12.0.0)
   - 4 MEDIUM (blocks minor 11.3.0 or upcoming)
   - 6 LOW (future)
4. Shows summary table with all categories
5. User selects "Fix all CRITICAL (overdue) deprecations"
6. Analyses first overdue deprecation:
   - File: plugins/modules/s3_object.py line 1375
   - Warning added for passing both dualstack and endpoint_url
   - Deprecated since 2024-12-01 (now 115 days overdue)
   - Should remove the compatibility shim
7. Implements the fix:
   - Removes the deprecation warning
   - Removes the if block that allowed both parameters
   - Adds validation to fail if both are provided
8. Runs precommit checks
9. Creates changelog fragment as breaking change
10. Commits with descriptive message
11. Asks about PR creation
12. Returns to step 6 for remaining 2 overdue deprecations

### Example 2: Preparing for Major Release (Version-based)

User: "We're preparing for the 12.0.0 major release. Run /cleanup-deprecations"

Skill:
1. Determines current version: 11.2.0, next minor: 11.3.0, next major: 12.0.0
2. Searches codebase for all deprecation warnings
3. Finds 5 deprecations marked with `version="12.0.0"` (HIGH priority - blocks major)
4. Shows summary highlighting the HIGH priority items
5. User selects "Fix all HIGH (blocks major) deprecations"
6. Processes all 5 deprecations that would block 12.0.0:
   - plugins/modules/ec2_instance.py - Remove `count` parameter (use `exact_count` instead)
   - plugins/modules/rds_instance.py - Remove `purge_cloudwatch_logs_exports` default behaviour change
   - plugins/modules/s3_bucket.py - Remove `policy` parameter (use `amazon.aws.s3_bucket_policy` module)
   - plugins/module_utils/ec2.py - Remove legacy `get_aws_connection_info()` function
   - plugins/inventory/aws_ec2.py - Remove `hostname` variable (use `inventory_hostname` instead)
7. For each deprecation:
   - Removes deprecated code paths
   - Updates documentation
   - Removes or updates integration tests
   - Creates changelog fragments (all as breaking_changes)
8. Runs full prepush checks (includes integration tests)
9. Creates single PR: "Remove all deprecations scheduled for 12.0.0"
10. PR is tagged with `breaking-change` and `major-release-blocker`
11. Once merged, version 12.0.0 can be released

### Example 3: Checking Deprecations Before Minor Release

User: "Check if there are any deprecations blocking the 11.3.0 minor release"

Skill:
1. Determines next minor: 11.3.0
2. Searches for `version="11.3.0"` deprecations
3. Finds 2 deprecations marked for 11.3.0 (MEDIUM priority)
4. Shows these as blockers for the minor release
5. User addresses both before cutting the 11.3.0 release

## Search Patterns

### Common deprecation patterns to search for:

```bash
# Module deprecations
grep -rn "module\.deprecate(" plugins/modules/ --include="*.py"

# Module_utils deprecations
grep -rn "display\.deprecated(" plugins/module_utils/ --include="*.py"

# Inventory plugin deprecations
grep -rn "self\.deprecate(" plugins/inventory/ --include="*.py"

# Lookup plugin deprecations
grep -rn "display\.deprecated(" plugins/lookup/ --include="*.py"

# Find date-based deprecations
grep -rn 'date=' plugins/ --include="*.py" | grep deprecate

# Find version-based deprecations
grep -rn 'version=' plugins/ --include="*.py" | grep deprecate
```

## Output Format

When presenting deprecation details:

```
=============================================================================
Overdue Deprecation Details
=============================================================================

File: plugins/modules/s3_object.py
Line: 1374-1382
Days Overdue: 115 (removal date was 2024-12-01)
Type: Parameter compatibility

CODE CONTEXT:
-------------
    if dualstack and endpoint_url:
        module.deprecate(
            (
                "Support for passing both the 'dualstack' and 'endpoint_url' parameters at the same "
                "time has been deprecated."
            ),
            date="2024-12-01",
            collection_name="amazon.aws",
        )
        if "amazonaws.com" not in endpoint_url:
            module.fail_json(msg="dualstack only applies to AWS S3")

DEPRECATION MESSAGE:
-------------------
"Support for passing both the 'dualstack' and 'endpoint_url' parameters at the same
time has been deprecated."

SUGGESTED FIX:
-------------
1. Remove the deprecation warning (lines 1375-1382)
2. Remove the special handling that allows both parameters together
3. Add validation to fail if both dualstack and endpoint_url are provided:

   if dualstack and endpoint_url:
       module.fail_json(
           msg="Parameters 'dualstack' and 'endpoint_url' are mutually exclusive. "
               "Use endpoint_url with a dualstack endpoint instead."
       )

BREAKING CHANGE IMPACT:
----------------------
- Users passing both dualstack=True and endpoint_url will get an error
- This was already deprecated behaviour
- Users should remove dualstack parameter and use proper dualstack endpoints in endpoint_url

MIGRATION GUIDE:
---------------
Before:
  dualstack: true
  endpoint_url: "https://s3.us-east-1.amazonaws.com"

After:
  endpoint_url: "https://s3.dualstack.us-east-1.amazonaws.com"
```
