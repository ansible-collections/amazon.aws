---
name: next-version
description: Determine the next major/minor/patch release version for version_added tags
---

<!--
This skill helps determine what version to use in version_added tags when documenting
new features, parameters, or modules. It follows Semantic Versioning (SemVer).
-->

# Next Version Workflow

Determine the next release version numbers based on stable branches and git tags:

1. **Determine current major version**:
   - Run `git branch -r | grep -o 'stable-[0-9]\+' | grep -o '[0-9]\+' | sort -n | tail -1` to find the highest stable branch number
   - This gives the current major version (e.g., if `stable-2` exists, current major is 2)
   - If no stable branches exist, current major is 0 (pre-1.0 releases)

2. **Find latest tag for current major**:
   - Run `git tag --list --sort=-version:refname | grep '^<major>\.' | head -1` (replacing `<major>` with the current major version)
   - This finds the most recent release tag for the current major version
   - Parse it to extract major, minor, and patch numbers

3. **Calculate next versions**:
   - **Next patch**: `major.minor.(patch+1)` - For bugfixes only, rarely used in version_added
   - **Next minor**: `major.(minor+1).0` - For new features (most common for version_added)
   - **Next major**: `(major+1).0.0` - For breaking changes

4. **Present the versions** with guidance:
   ```
   Current stable branch: stable-X
   Current version: X.Y.Z

   Next versions:
   - Patch (X.Y.Z+1): For bugfixes - rarely needed in version_added tags
   - Minor (X.Y+1.0): For new features - use this for new parameters, modules, or functionality
   - Major (X+1.0.0): For breaking changes - use this for backwards-incompatible changes

   Most common: Use the next minor version (X.Y+1.0) for version_added tags on new features.
   ```

**Note**: This follows Semantic Versioning where:
- Patch releases (X.Y.Z): Bugfixes and security fixes
- Minor releases (X.Y.0): New features that are backwards-compatible
- Major releases (X.0.0): Breaking changes

**Stable branches**: The stable-X branches indicate the current major version. Patch releases on older major versions may be more recent than the latest minor release, so we use the stable branch to determine which major version to base calculations on.
