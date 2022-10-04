# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.cloud import CloudRetry


def test_found_not_itterable():
    assert CloudRetry.found('404', 5) is False
    assert CloudRetry.found('404', None) is False
    assert CloudRetry.found('404', 404) is False
    # This seems counter intuitive, but the second argument is supposed to be iterable...
    assert CloudRetry.found(404, 404) is False


def test_found_no_match():
    assert CloudRetry.found('404', ['403']) is False
    assert CloudRetry.found('404', ['500', '403']) is False
    assert CloudRetry.found('404', {'403'}) is False
    assert CloudRetry.found('404', {'500', '403'}) is False


def test_found_match():
    assert CloudRetry.found('404', ['404']) is True
    assert CloudRetry.found('404', ['403', '404']) is True
    assert CloudRetry.found('404', ['404', '403']) is True
    assert CloudRetry.found('404', {'404'}) is True
    assert CloudRetry.found('404', {'403', '404'}) is True
    # Beware, this will generally only work with strings (they're iterable)
    assert CloudRetry.found('404', '404') is True
