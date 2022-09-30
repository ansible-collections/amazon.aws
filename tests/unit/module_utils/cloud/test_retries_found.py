# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.cloud import CloudRetry


class TestRetriesFound:

    def setup_method(self):
        pass

    def test_found_not_itterable(self):
        assert CloudRetry.found('404', 5) is False
        assert CloudRetry.found('404', None) is False

    def test_found_no_match(self):
        assert CloudRetry.found('404', ['403']) is False
        assert CloudRetry.found('404', ['500', '403']) is False

    def test_found_match(self):
        assert CloudRetry.found('404', ['404']) is True
        assert CloudRetry.found('404', ['403', '404']) is True
        assert CloudRetry.found('404', ['404', '403']) is True
        assert CloudRetry.found('404', {'404'}) is True
        assert CloudRetry.found('404', {'403', '404'}) is True
