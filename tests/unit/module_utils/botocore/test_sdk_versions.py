# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
import warnings
from unittest.mock import sentinel

try:
    import botocore
    import boto3
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.botocore import botocore_at_least
from ansible_collections.amazon.aws.plugins.module_utils.botocore import boto3_at_least

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleBotocoreError

from ansible_collections.amazon.aws.plugins.module_utils import botocore as botocore_utils

DUMMY_VERSION = "5.5.5.5"

TEST_VERSIONS = [
    ["1.1.1", "2.2.2", True],
    ["1.1.1", "0.0.1", False],
    ["9.9.9", "9.9.9", True],
    ["9.9.9", "9.9.10", True],
    ["9.9.9", "9.10.9", True],
    ["9.9.9", "10.9.9", True],
    ["9.9.9", "9.9.8", False],
    ["9.9.9", "9.8.9", False],
    ["9.9.9", "8.9.9", False],
    ["10.10.10", "10.10.10", True],
    ["10.10.10", "10.10.11", True],
    ["10.10.10", "10.11.10", True],
    ["10.10.10", "11.10.10", True],
    ["10.10.10", "10.10.9", False],
    ["10.10.10", "10.9.10", False],
    ["10.10.10", "9.19.10", False],
]

if not HAS_BOTO3:
    pytest.mark.skip(
        "test_require_at_least.py requires the python modules 'boto3' and 'botocore'", allow_module_level=True
    )


# ========================================================
#   Test gather_sdk_versions
# ========================================================
def test_gather_sdk_versions_missing_botocore(monkeypatch):
    monkeypatch.setattr(botocore_utils, "HAS_BOTO3", False)
    sdk_versions = botocore_utils.gather_sdk_versions()
    assert isinstance(sdk_versions, dict)
    assert sdk_versions == {}


def test_gather_sdk_versions(monkeypatch):
    monkeypatch.setattr(botocore_utils, "HAS_BOTO3", True)
    monkeypatch.setattr(botocore, "__version__", sentinel.BOTOCORE_VERSION)
    monkeypatch.setattr(boto3, "__version__", sentinel.BOTO3_VERSION)

    sdk_versions = botocore_utils.gather_sdk_versions()
    assert isinstance(sdk_versions, dict)
    assert len(sdk_versions) == 2
    assert "boto3_version" in sdk_versions
    assert "botocore_version" in sdk_versions
    assert sdk_versions["boto3_version"] is sentinel.BOTO3_VERSION
    assert sdk_versions["botocore_version"] is sentinel.BOTOCORE_VERSION


# ========================================================
#   Test botocore_at_least
# ========================================================
@pytest.mark.parametrize("desired_version, compare_version, at_least", TEST_VERSIONS)
def test_botocore_at_least(monkeypatch, desired_version, compare_version, at_least):
    monkeypatch.setattr(botocore, "__version__", compare_version)
    # Set boto3 version to a known value (tests are on both sides) to make
    # sure we're comparing the right library
    monkeypatch.setattr(boto3, "__version__", DUMMY_VERSION)

    assert at_least == botocore_at_least(desired_version)


# ========================================================
#   Test boto3_at_least
# ========================================================
@pytest.mark.parametrize("desired_version, compare_version, at_least", TEST_VERSIONS)
def test_boto3_at_least(monkeypatch, desired_version, compare_version, at_least):
    # Set botocore version to a known value (tests are on both sides) to make
    # sure we're comparing the right library
    monkeypatch.setattr(botocore, "__version__", DUMMY_VERSION)
    monkeypatch.setattr(boto3, "__version__", compare_version)

    assert at_least == boto3_at_least(desired_version)


# ========================================================
#   Test check_sdk_version_supported
# ========================================================
def test_check_sdk_missing_botocore(monkeypatch):
    monkeypatch.setattr(botocore_utils, "HAS_BOTO3", False)

    with pytest.raises(AnsibleBotocoreError) as exception:
        botocore_utils.check_sdk_version_supported()

    assert "botocore and boto3" in exception.value.message

    with warnings.catch_warnings():
        # We should be erroring out before we get as far as testing versions
        # so fail if a warning is emitted
        warnings.simplefilter("error")
        with pytest.raises(AnsibleBotocoreError) as exception:
            botocore_utils.check_sdk_version_supported(warn=warnings.warn)

    assert "botocore and boto3" in exception.value.message


def test_check_sdk_all_good(monkeypatch):
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTOCORE_VERSION", "6.6.6")
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTO3_VERSION", "6.6.6")
    monkeypatch.setattr(boto3, "__version__", "6.6.6")
    monkeypatch.setattr(botocore, "__version__", "6.6.6")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported()

    assert supported is True

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)

    assert supported is True


def test_check_sdk_all_good_override(monkeypatch):
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTOCORE_VERSION", "6.6.6")
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTO3_VERSION", "6.6.6")
    monkeypatch.setattr(boto3, "__version__", "5.5.5")
    monkeypatch.setattr(botocore, "__version__", "5.5.5")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported(
            botocore_version="5.5.5",
            boto3_version="5.5.5",
        )

    assert supported is True

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported(
            botocore_version="5.5.5",
            boto3_version="5.5.5",
            warn=warnings.warn,
        )

    assert supported is True


@pytest.mark.parametrize("desired_version, compare_version, at_least", TEST_VERSIONS)
def test_check_sdk_botocore(monkeypatch, desired_version, compare_version, at_least):
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTOCORE_VERSION", desired_version)
    monkeypatch.setattr(botocore, "__version__", compare_version)
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTO3_VERSION", DUMMY_VERSION)
    monkeypatch.setattr(boto3, "__version__", DUMMY_VERSION)

    # Without warn being passed we should just return False
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported()

    assert supported is at_least

    if supported:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)
    else:
        with pytest.warns(UserWarning, match="botocore") as recorded_warnings:
            supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)
        assert len(recorded_warnings) == 1
        w = recorded_warnings.pop(UserWarning)
        assert "boto3" not in str(w.message)

    assert supported is at_least


@pytest.mark.parametrize("desired_version, compare_version, at_least", TEST_VERSIONS)
def test_check_sdk_boto3(monkeypatch, desired_version, compare_version, at_least):
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTO3_VERSION", desired_version)
    monkeypatch.setattr(boto3, "__version__", compare_version)
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTOCORE_VERSION", DUMMY_VERSION)
    monkeypatch.setattr(botocore, "__version__", DUMMY_VERSION)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported()

    assert supported is at_least

    if supported:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)
    else:
        with pytest.warns(UserWarning, match="boto3") as recorded_warnings:
            supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)
        assert len(recorded_warnings) == 1
        w = recorded_warnings.pop(UserWarning)
        assert "boto3" in str(w.message)

    assert supported is at_least


@pytest.mark.parametrize("desired_version, compare_version, at_least", TEST_VERSIONS)
def test_check_sdk_both(monkeypatch, desired_version, compare_version, at_least):
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTO3_VERSION", desired_version)
    monkeypatch.setattr(boto3, "__version__", compare_version)
    monkeypatch.setattr(botocore_utils, "MINIMUM_BOTOCORE_VERSION", desired_version)
    monkeypatch.setattr(botocore, "__version__", compare_version)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        supported = botocore_utils.check_sdk_version_supported()
    assert supported is at_least

    if supported:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)
    else:
        message_map = dict()
        with pytest.warns(UserWarning) as recorded_warnings:
            supported = botocore_utils.check_sdk_version_supported(warn=warnings.warn)
        assert len(recorded_warnings) == 2
        for w in recorded_warnings:
            if "boto3" in str(w.message):
                message_map["boto3"] = str(w.message)
            elif "botocore" in str(w.message):
                message_map["botocore"] = str(w.message)
        assert "boto3" in message_map
        assert "botocore" in message_map
    assert supported is at_least
