# Update Requirements Workflow

Update minimum Python, boto3, and botocore version requirements for the collection.

This workflow is used periodically when AWS SDK for Python drops support for older Python versions or when bumping minimum boto3/botocore versions for a major release.

## Overview

This skill updates all files that reference minimum version requirements and creates appropriate changelog fragments for breaking changes and deprecations.

## When to Use

Use this skill when:
- AWS drops support for a Python version
- Planning a major release with updated minimum requirements
- Needing to bump boto3/botocore minimum versions

**Typical schedule:**
- Python versions: Follow AWS SDK Python Support Policy (typically annually)
- boto3/botocore: Major releases, or when adopting features from newer SDK versions

## Workflow

### 1. Determine New Versions

Ask the user what the new minimum versions should be, or help determine them:

**For Python version:**
- Check AWS SDK Python Support Policy: https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/
- Note: Ansible-core minimum version already sets a floor (e.g., ansible-core 2.17 requires Python 3.10+)

**For boto3/botocore versions:**
- Option 1: User specifies desired version
- Option 2: Look up versions in local clones of the botocore and boto3 repos:

  **Step 1: Update repos (optional but recommended):**
  ```bash
  cd <path-to-botocore-repo>
  git fetch --tags
  cd <path-to-boto3-repo>
  git fetch --tags
  cd <path-to-aiobotocore-repo>
  git fetch --tags
  ```
  Skip this step if repos don't exist or can't be updated.

  **Step 2: Look up versions:**
  ```bash
  cd <path-to-botocore-repo>
  # Find minor releases around target date
  git log --tags --simplify-by-decoration --pretty="format:%ai %d" | grep -E '1\.[0-9]+\.0'
  # Check changelog for Python support changes
  git show <version>:CHANGELOG.rst | head -100
  ```
  Note: If you have local clones of the AWS SDK repos, their locations may be documented in your ~/.claude/CLAUDE.md

**For aiobotocore version (in requirements.txt):**
- **CRITICAL:** aiobotocore must be compatible with the botocore version
- aiobotocore uses tight version pinning (e.g., `botocore >=1.38.23, <1.38.28`)
- To find compatible version, check local aiobotocore repo (if available):
  ```bash
  cd <path-to-aiobotocore-repo>
  git fetch --tags
  # Find versions with compatible botocore ranges
  git tag -l '2.*' | while read tag; do
    echo "=== $tag ==="
    git show $tag:pyproject.toml | grep -A 5 'dependencies'
  done
  ```
- Look for an aiobotocore version where the botocore minimum is ≤ your target and maximum is > your target
- **Common issue:** aiobotocore may not support the .0 release immediately (e.g., no support for 1.38.0 but 2.23.0 supports >=1.38.23)
- **If incompatible:** Either wait for a compatible aiobotocore release or adjust botocore target version upward
- Note: Repo location may be documented in ~/.claude/CLAUDE.md

**For awscli version (in constraints files):**
- **WARNING:** awscli version is determined by the dependency chain, NOT a simple formula
- The old pattern "botocore 1.X.0 → awscli 1.(X-1).0" is INCORRECT and will cause conflicts
- awscli version must be compatible with BOTH:
  1. The target botocore version
  2. The aiobotocore version's awscli requirements
- Process:
  1. Find aiobotocore version compatible with target botocore (see above)
  2. Check aiobotocore's pyproject.toml for awscli requirement (e.g., `awscli >= 1.40.22, < 1.40.27`)
  3. Find an awscli version in that range
  4. Verify that awscli version's botocore dependency is compatible with target botocore
- Example chain:
  - Target: botocore 1.38.x
  - aiobotocore 2.23.0 requires: botocore >= 1.38.23, awscli >= 1.40.22
  - awscli 1.40.23 requires: botocore == 1.38.24
  - Result: Must use botocore 1.38.24, boto3 1.38.24, aiobotocore 2.23.0, awscli 1.40.23

### 2. Confirm Breaking Change Details

Ask the user:
- Target collection version (e.g., 12.0.0)
- Forecast release date (e.g., early May 2026)
- Next deprecation timeline (when will the NEW minimum version be deprecated?)

### 3. Create Feature Branch

Create a feature branch before making any changes:
```bash
git checkout main
git fetch origin
git reset --hard origin/main
git checkout -b requirements/python<ver>-boto<ver> origin/main
git branch --unset-upstream
```

Example: `requirements/python39-boto138`

### 4. Update All Files

Update version numbers in these files:

**a) requirements.txt**
```
botocore>=X.Y.0   # Use the minimum .0 version (e.g., 1.38.0)
boto3>=X.Y.0      # Use the minimum .0 version (e.g., 1.38.0)
aiobotocore>=X.Z.0  # Use the minimum compatible version
```

**Note:** requirements.txt uses the .0 versions to declare minimum support, even though testing uses higher patch versions.

**b) tests/unit/constraints.txt**
```
# Note: Using X.Y.Z instead of X.Y.0 due to aiobotocore/awscli compatibility.
# aiobotocore A.B.C (earliest version supporting botocore X.Y.x) requires botocore>=X.Y.Z
# awscli M.N.O (required by aiobotocore A.B.C) requires botocore==X.Y.Z
botocore==X.Y.Z     # Actual version determined by dependency chain
boto3==X.Y.Z        # Match botocore version
aiobotocore==A.B.C  # Earliest version supporting botocore X.Y.x

# AWS CLI has `botocore==` dependencies, provide the one that matches botocore
# to avoid needing to download over a years worth of awscli wheels.
# Note: awscli version determined from aiobotocore A.B.C compatibility (requires awscli>=M.N.O)
awscli==M.N.O
```

**c) tests/integration/constraints.txt**
```
# Note: Using X.Y.Z instead of X.Y.0 due to aiobotocore/awscli compatibility.
# aiobotocore A.B.C (earliest version supporting botocore X.Y.x) requires botocore>=X.Y.Z
# awscli M.N.O (required by aiobotocore A.B.C) requires botocore==X.Y.Z
botocore==X.Y.Z     # Actual version determined by dependency chain
boto3==X.Y.Z        # Match botocore version

# AWS CLI has `botocore==` dependencies, provide the one that matches botocore
# to avoid needing to download over a years worth of awscli wheels.
# Note: awscli version determined from aiobotocore A.B.C compatibility (requires awscli>=M.N.O)
awscli==M.N.O
```

**IMPORTANT:** The constraint files will likely use a higher patch version than .0 due to aiobotocore compatibility. Include comments explaining why.

**d) plugins/module_utils/botocore.py**
```python
MINIMUM_BOTOCORE_VERSION = "X.Y.0"
MINIMUM_BOTO3_VERSION = "X.Y.0"
```

**e) README.md**

Update the "Python version compatibility" section:
```markdown
### Python version compatibility

This collection depends on the AWS SDK for Python (Boto3 and Botocore).  Due to the
[AWS SDK Python Support Policy](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/)
this collection requires Python X.Y or greater.

Amazon has also announced the planned end of support for
[Python versions below X.Z](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/).
As such, support for Python versions below X.Z will be removed in a release after YYYY-MM-DD.
```

Update the "AWS SDK version compatibility" section:
```markdown
Version X.0.0 of this collection supports `boto3 >= X.Y.0` and `botocore >= X.Y.0`
```

**f) tests/unit/plugins/module_utils/modules/ansible_aws_module/test_minimal_versions.py**

Update the version constants to match new minimum versions and set OLD versions to the previous minor version (e.g., 1.38.0 → OLD is 1.37.999).

### 5. Determine Actual Constraint Versions

**CRITICAL:** Due to aiobotocore/awscli dependency chains, the constraint files will use higher patch versions than .0

Process:
1. Find aiobotocore version compatible with target botocore X.Y.0 (from step 1)
2. Check aiobotocore's required botocore minimum (likely X.Y.Z where Z > 0)
3. Check aiobotocore's required awscli range (e.g., awscli >= M.N.O, < M.N.P)
4. Find awscli version in that range (e.g., M.N.O)
5. Check that awscli's botocore dependency (often exact pin like botocore==X.Y.W)
6. Use the highest patch version from the chain as your constraint version

Example for botocore 1.38.0:
- aiobotocore 2.23.0 requires: botocore >= 1.38.23
- aiobotocore 2.23.0 requires: awscli >= 1.40.22, < 1.40.27
- awscli 1.40.23 requires: botocore == 1.38.24
- Result: Use botocore 1.38.24 in constraints (not 1.38.0 or 1.38.23)

### 6. Test Dependency Installation

**CRITICAL:** Verify the chosen constraint versions can install together:

```bash
# Test in a temporary virtual environment with CONSTRAINT versions
python -m venv /tmp/test-requirements
source /tmp/test-requirements/bin/activate
pip install "botocore==X.Y.Z" "boto3==X.Y.Z" "aiobotocore==A.B.C" "awscli==M.N.O"
deactivate
rm -rf /tmp/test-requirements
```

If this fails with dependency conflicts, re-examine the dependency chain. **Do not proceed if dependencies cannot install together.**

### 7. Verify Version Consistency

After updating all files, verify versions are consistent:

```bash
# Check requirements.txt has .0 versions
grep -E "botocore>=|boto3>=|aiobotocore>=" requirements.txt

# Check constraints have actual test versions (likely higher patch)
grep -E "botocore==|boto3==|aiobotocore==|awscli==" tests/unit/constraints.txt tests/integration/constraints.txt

# Check botocore.py has .0 versions
grep "MINIMUM_" plugins/module_utils/botocore.py

# Verify no files still reference the OLD version (e.g., 1.35.0)
grep -r "1\.35\.0" requirements.txt tests/unit/constraints.txt tests/integration/constraints.txt plugins/module_utils/botocore.py
```

Expected results:
- requirements.txt: Uses X.Y.0 versions (e.g., >=1.38.0)
- Constraint files: Use actual testable versions (e.g., ==1.38.24) with explanatory comments
- botocore.py: Uses X.Y.0 versions (e.g., "1.38.0")
- test_minimal_versions.py: Uses X.Y.0 for MINIMAL_*, old minor for OLD_* (e.g., 1.37.999)
- No old version numbers remain except in test_minimal_versions.py OLD_* constants

### 8. Search for Other Version References

Search the entire codebase for any other references to the old versions:

```bash
# Search for old boto3/botocore version references
grep -r "1\.35\.0" . --exclude-dir=.git --exclude-dir=.tox --exclude-dir="*.egg-info"

# Also check for old Python version references (e.g., 3.8)
grep -ri "python.*3\.8" . --exclude-dir=.git --exclude-dir=.tox --exclude-dir="*.egg-info"
```

Review results and update any documentation, comments, or other references as needed.

### 9. Create Changelog Fragment

Use the `changelog` skill to create a changelog fragment with both breaking_changes and deprecated_features sections.

**Sections to include:**
- `breaking_changes`: For the new minimum Python, boto3, and botocore versions
- `deprecated_features`: For the deprecation notice about the next Python version to be dropped

**Example content:**
- Breaking: Minimum supported Python version is now X.Y
- Breaking: Minimum supported boto3 version is now X.Y.0
- Breaking: Minimum supported botocore version is now X.Y.0
- Deprecated: Support for Python X.Y will be removed in a release after YYYY-MM-DD

The `changelog` skill will handle proper formatting and filename generation.

### 10. Verify tox.ini Alignment

Check that `tox.ini` envlist aligns with the new requirements:

```ini
[tox]
envlist =
    ansible{2.17}-py{310,311,312}-{with_constraints,without_constraints}
    ...
```

Ensure:
- Lowest Python version tested matches or exceeds new minimum
- No Python versions below the new minimum are being tested

**Note:** Usually no changes needed since Ansible-core minimum already sets the floor.

### 11. Run Pre-commit Checks

Use the `precommit` skill to run format, lint, and unit tests.

**IMPORTANT:** All tests must pass before committing. Unit tests are essential to verify the test_minimal_versions.py updates are correct.

If unit tests fail, check that the test_minimal_versions.py file was updated correctly with the new minimum versions.

### 12. Commit Changes

**Only proceed once all tests pass.**

Commit the changes with a descriptive message:
```
Bump minimum Python and boto3/botocore requirements

Bump minimum requirements to Python X.Y, boto3 X.Y.0, and botocore X.Y.0
following AWS SDK for Python's end of support for Python X.Z (<month> YYYY).

Changes:
- requirements.txt: boto3>=X.Y.0, botocore>=X.Y.0, aiobotocore>=A.B.C
- tests/unit/constraints.txt: boto3==X.Y.Z, botocore==X.Y.Z, aiobotocore==A.B.C, awscli==M.N.O
- tests/integration/constraints.txt: boto3==X.Y.Z, botocore==X.Y.Z, awscli==M.N.O
- plugins/module_utils/botocore.py: MINIMUM_BOTO3_VERSION, MINIMUM_BOTOCORE_VERSION
- tests/unit/.../test_minimal_versions.py: Update version test constants
- README.md: Update Python requirement to X.Y+, add Python X.Z+ note for <date>
- changelogs/fragments/<name>.yml: Breaking changes and deprecation warnings

Note: Constraint files use boto3/botocore X.Y.Z (not X.Y.0) due to aiobotocore/awscli
dependency requirements. See constraint file comments for details.

boto3 and botocore X.Y.0 were released on YYYY-MM-DD and officially
dropped Python X.Z support.

Note: Ansible-core X.Y+ (minimum supported version) already requires
Python X.Z+. The collection now requires Python X.Y+ to align with
AWS SDK requirements, though Ansible itself requires X.Z+.

Amazon will drop support for Python X.Y in <month> YYYY, so support for
Python versions below X.Z will be removed in a release after YYYY-MM-DD.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Then use the `create-pr` skill to create the pull request. The skill will:
- Run prepush checks (format, lint, unit tests on oldest/newest, sanity tests)
- Push to the remote
- Create a draft PR with appropriate labels (including `do_not_backport` for breaking changes)
- Automatically update changelog fragments with the PR URL

**Suggested PR details for the `create-pr` skill:**
- **Title:** `Bump minimum Python and boto3/botocore requirements`
- **Summary:** Note this is in preparation for vX.0.0, mention version changes and AWS SDK deprecation dates
- **Issue type:** Breaking Change Pull Request
- **Component:** Collection requirements
- **Additional info:** Note aiobotocore compatibility and Ansible-core version alignment

## Important Notes

### Version Alignment

- **Python minimum:** Should align with AWS SDK support, but note Ansible-core may require higher
- **boto3/botocore:** Must match exactly (same version number)
- **aiobotocore:** Must be compatible with botocore version - check PyPI for compatibility
- **awscli:** Typically lags botocore by 1 minor version (botocore 1.38.0 → awscli 1.37.0)

### Deprecation Timeline

Follow AWS SDK deprecation dates plus ~1 year:
- AWS drops Python X.Y in YYYY-MM → Collection drops in (YYYY+1)-MM

Example:
- AWS drops Python 3.8 in 2025-04 → Collection drops in release after 2026-05-01
- AWS drops Python 3.9 in 2026-04 → Collection drops in release after 2027-04-01

### Testing Considerations

- **Must run unit tests** to verify test_minimal_versions.py updates are correct
- Format and lint must pass
- Consider running integration tests if time permits
- CI will test with matrix of Python/Ansible versions

### Common Pitfalls

1. **Working on main branch:** Create feature branch first (step 3) before making any changes
2. **Incompatible aiobotocore:** MUST verify aiobotocore compatibility with botocore (step 5) - integration tests will fail if incompatible
3. **Forgetting aiobotocore:** Must update aiobotocore in requirements.txt, not just boto3/botocore
4. **Forgetting awscli version:** Remember to update in constraints files
5. **Inconsistent versions:** All files must be updated together - use verification step (step 6)
6. **Missing test file update:** Must update test_minimal_versions.py or unit tests will fail
7. **Not searching for other references:** Old versions may exist in docs/comments (step 7)
8. **Missing deprecation notice:** Always include for the NEW minimum version in the changelog fragment
9. **Wrong README wording:** Use "below X.Y" not "X.Y and below"

## Example: Python 3.8 → 3.9, boto 1.35.0 → 1.38.0

**Context:**
- Target: v12.0.0, early May 2026
- boto3/botocore 1.38.0 dropped Python 3.8 on 2025-04-22
- AWS will drop Python 3.9 in April 2026

**Changes:**
- Python: 3.8+ → 3.9+
- boto3: 1.35.0 → 1.38.0
- botocore: 1.35.0 → 1.38.0
- awscli: 1.34.0 → 1.37.0 (in constraints)

**Deprecation:**
- Python 3.9 support removal after 2027-04-01

**Files:** 7 files updated (requirements.txt, 2 constraints files, botocore.py, README.md, test_minimal_versions.py, changelog fragment)

**Branch:** `requirements/python39-boto138`

## Future Enhancements

- Automate version lookup from boto repos
- Integration with release planning tools
- Automated script to update all version numbers at once
