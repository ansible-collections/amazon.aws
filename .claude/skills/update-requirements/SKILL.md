# Update Requirements Workflow

Update minimum Python, boto3, and botocore version requirements for the collection.

## Overview

This skill updates all files that reference minimum version requirements and creates appropriate changelog fragments for breaking changes and deprecations. Used when AWS SDK drops support for older Python versions or when bumping minimum boto3/botocore versions for a major release.

## When to Use

- AWS drops support for a Python version
- Planning a major release with updated minimum requirements
- Needing to bump boto3/botocore minimum versions

**Typical schedule:**
- Python versions: Follow AWS SDK Python Support Policy (annually)
- boto3/botocore: Major releases, or when adopting features from newer SDK versions

## Workflow

### 1. Determine New Versions

Ask the user what the new minimum versions should be, or help determine them:

**Python version:**
- Check AWS SDK Python Support Policy
- Note: Ansible-core minimum version already sets a floor (e.g., ansible-core 2.17 requires Python 3.10+)

**boto3/botocore versions:**
- User specifies desired version, OR
- Look up in local AWS SDK repos (if available, locations may be in ~/.claude/CLAUDE.md):
  ```bash
  cd <path-to-botocore-repo>
  git fetch --tags
  git log --tags --simplify-by-decoration --pretty="format:%ai %d" | grep -E '1\.[0-9]+\.0'
  ```

**aiobotocore version (CRITICAL):**
- aiobotocore must be compatible with botocore version
- Uses tight version pinning (e.g., `botocore >=1.38.23, <1.38.28`)
- Check local aiobotocore repo (if available):
  ```bash
  cd <path-to-aiobotocore-repo>
  git fetch --tags
  git tag -l '2.*' | while read tag; do
    echo "=== $tag ==="
    git show $tag:pyproject.toml | grep -A 5 'dependencies'
  done
  ```
- Find version where botocore minimum is ≤ target and maximum is > target
- **Common issue:** aiobotocore may not support the .0 release immediately

**awscli version (WARNING):**
- Determined by dependency chain, NOT a simple formula
- Must be compatible with BOTH target botocore AND aiobotocore's awscli requirements
- Process:
  1. Find aiobotocore version compatible with target botocore
  2. Check aiobotocore's pyproject.toml for awscli requirement
  3. Find awscli version in that range
  4. Verify awscli's botocore dependency is compatible

### 2. Confirm Breaking Change Details

Ask the user:
- Target collection version (e.g., 12.0.0)
- Forecast release date (e.g., early May 2026)
- Next deprecation timeline (when will NEW minimum be deprecated?)

### 3. Create Feature Branch

Use the `new-branch` skill to create a new feature branch.

Suggested branch name: `requirements/python<ver>-boto<ver>` (e.g., `requirements/python39-boto138`)

### 4. Update All Files

**a) requirements.txt** - Use .0 versions:
```
botocore>=X.Y.0
boto3>=X.Y.0
aiobotocore>=X.Z.0
```

**b) tests/unit/constraints.txt** and **tests/integration/constraints.txt** - Use actual testable versions with explanatory comments:
```
# Note: Using X.Y.Z instead of X.Y.0 due to aiobotocore/awscli compatibility.
# aiobotocore A.B.C (earliest version supporting botocore X.Y.x) requires botocore>=X.Y.Z
# awscli M.N.O (required by aiobotocore A.B.C) requires botocore==X.Y.Z
botocore==X.Y.Z
boto3==X.Y.Z
aiobotocore==A.B.C

# AWS CLI has `botocore==` dependencies, provide the one that matches botocore
# Note: awscli version determined from aiobotocore A.B.C compatibility
awscli==M.N.O
```

**Note:** Constraint files use higher patch versions than .0 due to dependency chains.

**c) plugins/module_utils/botocore.py**:
```python
MINIMUM_BOTOCORE_VERSION = "X.Y.0"
MINIMUM_BOTO3_VERSION = "X.Y.0"
```

**d) README.md** - Update Python compatibility sections

**e) tests/unit/plugins/module_utils/modules/ansible_aws_module/test_minimal_versions.py** - Update version constants (OLD versions to previous minor)

### 5. Determine Actual Constraint Versions

**CRITICAL:** Due to aiobotocore/awscli dependency chains, constraint files use higher patch versions:

1. Find aiobotocore compatible with target botocore X.Y.0
2. Check aiobotocore's required botocore minimum (likely X.Y.Z where Z > 0)
3. Check aiobotocore's required awscli range
4. Find awscli version in that range
5. Verify awscli's botocore dependency
6. Use the highest patch version from chain as constraint version

Example for botocore 1.38.0:
- aiobotocore 2.23.0 requires: botocore >= 1.38.23
- aiobotocore 2.23.0 requires: awscli >= 1.40.22, < 1.40.27
- awscli 1.40.23 requires: botocore == 1.38.24
- Result: Use botocore 1.38.24 in constraints (not 1.38.0)

### 6. Test Dependency Installation

**CRITICAL:** Verify chosen constraint versions install together:

```bash
python -m venv /tmp/test-requirements
source /tmp/test-requirements/bin/activate
pip install "botocore==X.Y.Z" "boto3==X.Y.Z" "aiobotocore==A.B.C" "awscli==M.N.O"
deactivate
rm -rf /tmp/test-requirements
```

**Do not proceed if dependencies cannot install together.**

### 7. Verify Version Consistency

```bash
# Check requirements.txt has .0 versions
grep -E "botocore>=|boto3>=|aiobotocore>=" requirements.txt

# Check constraints have actual test versions
grep -E "botocore==|boto3==|aiobotocore==|awscli==" tests/unit/constraints.txt tests/integration/constraints.txt

# Check botocore.py has .0 versions
grep "MINIMUM_" plugins/module_utils/botocore.py

# Verify no old version references remain
grep -r "1\.35\.0" requirements.txt tests/unit/constraints.txt tests/integration/constraints.txt plugins/module_utils/botocore.py
```

Expected:
- requirements.txt: X.Y.0 versions
- Constraint files: Actual testable versions with comments
- botocore.py: X.Y.0 versions
- test_minimal_versions.py: X.Y.0 for MINIMAL_*, old minor for OLD_*

### 8. Verify tox.ini Alignment

Check that tox.ini envlist aligns with new requirements:
```ini
[tox]
envlist =
    ansible{2.17}-py{310,311,312}-{with_constraints,without_constraints}
```

Ensure lowest Python version matches or exceeds new minimum.

### 9. Create Changelog Fragment

Use `changelog` skill to create fragment with both sections:
- `breaking_changes`: New minimum Python, boto3, botocore versions
- `deprecated_features`: Deprecation notice for next Python version to drop

### 10. Run Pre-commit Checks and Commit

Use `precommit` skill - all tests must pass before committing.

**Commit message:**
```
Bump minimum Python and boto3/botocore requirements

Bump minimum requirements to Python X.Y, boto3 X.Y.0, and botocore X.Y.0
following AWS SDK for Python's end of support for Python X.Z (<month> YYYY).

Changes:
- requirements.txt: boto3>=X.Y.0, botocore>=X.Y.0, aiobotocore>=A.B.C
- tests/unit/constraints.txt: boto3==X.Y.Z, botocore==X.Y.Z, aiobotocore==A.B.C, awscli==M.N.O
- tests/integration/constraints.txt: boto3==X.Y.Z, botocore==X.Y.Z, awscli==M.N.O
- plugins/module_utils/botocore.py: MINIMUM versions
- tests/unit/.../test_minimal_versions.py: Update version test constants
- README.md: Update Python requirement
- changelogs/fragments/<name>.yml: Breaking changes and deprecation warnings

Note: Constraint files use boto3/botocore X.Y.Z (not X.Y.0) due to aiobotocore/awscli
dependency requirements. See constraint file comments for details.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### 11. Create Pull Request

Use `create-pr` skill with:
- **Title:** `Bump minimum Python and boto3/botocore requirements`
- **Summary:** Note preparation for vX.0.0, version changes, AWS SDK deprecation dates
- **Issue type:** Breaking Change Pull Request
- **Component:** Collection requirements
- **Additional info:** Note aiobotocore compatibility and Ansible-core alignment

## Important Notes

### Version Alignment
- **Python minimum:** Align with AWS SDK support (Ansible-core may require higher)
- **boto3/botocore:** Must match exactly
- **aiobotocore:** Must be compatible with botocore - check PyPI
- **awscli:** Determined by dependency chain, not formula

### Deprecation Timeline
Follow AWS SDK deprecation dates plus ~1 year:
- AWS drops Python X.Y in YYYY-MM → Collection drops in (YYYY+1)-MM

### Common Pitfalls
1. **Working on main branch:** Use `new-branch` skill to create feature branch first before changes
2. **Incompatible aiobotocore:** Verify compatibility - integration tests fail if wrong
3. **Forgetting aiobotocore:** Must update in requirements.txt
4. **Inconsistent versions:** All files must be updated together
5. **Missing test file update:** Must update test_minimal_versions.py or unit tests fail
6. **Missing deprecation notice:** Always include for NEW minimum in changelog
7. **Wrong awscli version:** Determined by dependency chain, not simple formula
