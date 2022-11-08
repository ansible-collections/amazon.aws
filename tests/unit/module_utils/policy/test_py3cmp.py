# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.policy import _py3cmp


def test_py3cmp_simple():
    assert _py3cmp(1, 1) == 0
    assert _py3cmp(1, 2) == -1
    assert _py3cmp(2, 1) == 1
    assert _py3cmp("1", "1") == 0
    assert _py3cmp("1", "2") == -1
    assert _py3cmp("2", "1") == 1
    assert _py3cmp("a", "a") == 0
    assert _py3cmp("a", "b") == -1
    assert _py3cmp("b", "a") == 1
    assert _py3cmp(("a",), ("a",)) == 0
    assert _py3cmp(("a",), ("b",)) == -1
    assert _py3cmp(("b",), ("a",)) == 1


def test_py3cmp_mixed():
    # Replicates the Python2 comparison behaviour of placing strings before tuples
    assert _py3cmp(("a",), "a") == 1
    assert _py3cmp("a", ("a",)) == -1

    assert _py3cmp(("a",), "b") == 1
    assert _py3cmp("b", ("a",)) == -1
    assert _py3cmp(("b",), "a") == 1
    assert _py3cmp("a", ("b",)) == -1

    # intended for use by _hashable_policy, so expects either a string or a tuple
    with pytest.raises(TypeError):
        _py3cmp((1,), 1)
    with pytest.raises(TypeError):
        _py3cmp(1, (1,))
