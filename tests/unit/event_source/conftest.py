# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.tests.unit.utils.event import ListQueue


@pytest.fixture
def eda_queue() -> ListQueue:
    return ListQueue()
