# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ast
from pathlib import Path

import pytest

from ansible_collections.amazon.aws.plugins.doc_fragments import boto3 as boto3_fragment

FRAGMENT_FILES = sorted(Path(boto3_fragment.__file__).parent.glob("*.py"))


@pytest.mark.parametrize("path", FRAGMENT_FILES, ids=lambda path: path.stem)
def test_fragment_is_static(path):
    # Docs tools read the sections without running the code, so each one must be a plain string.
    tree = ast.parse(path.read_text(encoding="utf-8"))
    (fragment,) = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ModuleDocFragment"]
    assert not [node for node in fragment.body if isinstance(node, ast.FunctionDef)]
    sections = [node for node in fragment.body if isinstance(node, ast.Assign)]
    assert sections
    for section in sections:
        assert isinstance(section.value, ast.Constant)
        assert isinstance(section.value.value, str)
