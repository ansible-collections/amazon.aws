# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# While it may seem appropriate to import our custom fixtures here, the pytest_ansible pytest plugin
# isn't as agressive as the ansible_test._util.target.pytest.plugins.ansible_pytest_collections plugin
# when it comes to rewriting the import paths and as such we can't import fixtures via their
# absolute import path or across collections.

# Outside of a full ansible-core run, the collection python loader isn't installed into
# sys.meta_path/sys.path_hooks by default, so e.g. connection_loader.get("amazon.aws.aws_ssm", ...)
# can silently fail and return None once *any* "ansible_collections.*" module has already been
# imported as a plain namespace package. This must run at import time (module scope), not inside
# pytest_configure(), because pytest imports every conftest.py along the collection path -
# including nested ones that import "ansible_collections.*" themselves - before pytest_configure()
# is invoked for any of them. init_plugin_loader() is idempotent: if the collection finder is
# already configured (e.g. by ansible-test) it just emits a Python warning and returns.
from ansible.plugins.loader import init_plugin_loader

init_plugin_loader()


def pytest_configure(config):
    """Register custom markers for ansible-test compatibility."""
    config.addinivalue_line("markers", "limit_memory: Mark test with memory limit for pytest-memray")
