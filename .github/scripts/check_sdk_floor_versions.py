#!/usr/bin/env python3
"""Assert that botocore/boto3/aiobotocore floor versions are in sync.

Used by .github/workflows/check-ee-requirements.yml to catch a bump to one
of the files below without the others, same shape as
check-unit-requirements.yml.
"""

import re
import sys
from pathlib import Path


def pin(path, pattern, label):
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        print(f"::error file={path}::could not find {label} in {path}")
        sys.exit(1)
    return match.group(1)


def main():
    constraints = "tests/test-constraints.in"
    ee_requirements = "meta/ee-requirements.txt"
    botocore_py = "plugins/module_utils/botocore.py"
    test_minimal = "tests/unit/plugins/module_utils/modules/ansible_aws_module/test_minimal_versions.py"
    integration_constraints = "tests/integration/constraints.txt"

    values = {
        ("test-constraints.in", "botocore"): pin(constraints, r"^botocore==([\d.]+)", "botocore=="),
        ("test-constraints.in", "boto3"): pin(constraints, r"^boto3==([\d.]+)", "boto3=="),
        ("test-constraints.in", "aiobotocore"): pin(constraints, r"^aiobotocore==([\d.]+)", "aiobotocore=="),
        ("test-constraints.in", "awscli"): pin(constraints, r"^awscli==([\d.]+)", "awscli=="),
        ("ee-requirements.txt", "botocore"): pin(ee_requirements, r"^botocore>=([\d.]+)", "botocore>="),
        ("ee-requirements.txt", "boto3"): pin(ee_requirements, r"^boto3>=([\d.]+)", "boto3>="),
        ("ee-requirements.txt", "aiobotocore"): pin(ee_requirements, r"^aiobotocore>=([\d.]+)", "aiobotocore>="),
        ("botocore.py", "botocore"): pin(
            botocore_py, r'MINIMUM_BOTOCORE_VERSION\s*=\s*"([\d.]+)"', "MINIMUM_BOTOCORE_VERSION"
        ),
        ("botocore.py", "boto3"): pin(botocore_py, r'MINIMUM_BOTO3_VERSION\s*=\s*"([\d.]+)"', "MINIMUM_BOTO3_VERSION"),
        ("test_minimal_versions.py", "botocore"): pin(
            test_minimal, r'MINIMAL_BOTOCORE\s*=\s*"([\d.]+)"', "MINIMAL_BOTOCORE"
        ),
        ("test_minimal_versions.py", "boto3"): pin(test_minimal, r'MINIMAL_BOTO3\s*=\s*"([\d.]+)"', "MINIMAL_BOTO3"),
        ("tests/integration/constraints.txt", "botocore"): pin(
            integration_constraints, r"^botocore==([\d.]+)", "botocore=="
        ),
        ("tests/integration/constraints.txt", "boto3"): pin(integration_constraints, r"^boto3==([\d.]+)", "boto3=="),
        ("tests/integration/constraints.txt", "aiobotocore"): pin(
            integration_constraints, r"^aiobotocore==([\d.]+)", "aiobotocore=="
        ),
        ("tests/integration/constraints.txt", "awscli"): pin(integration_constraints, r"^awscli==([\d.]+)", "awscli=="),
    }

    by_package = {}
    for (source, package), version in values.items():
        by_package.setdefault(package, {})[source] = version

    failed = False
    for package, sources in by_package.items():
        distinct = set(sources.values())
        if len(distinct) > 1:
            failed = True
            details = ", ".join(f"{source}={version}" for source, version in sources.items())
            print(f"::error::{package} floor version mismatch: {details}")
        else:
            version = next(iter(distinct))
            print(f"OK: {package} floor is {version} everywhere")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
