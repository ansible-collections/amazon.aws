# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# While it may seem appropriate to import our custom fixtures here, the pytest_ansible pytest plugin
# isn't as agressive as the ansible_test._util.target.pytest.plugins.ansible_pytest_collections plugin
# when it comes to rewriting the import paths and as such we can't import fixtures via their
# absolute import path or across collections.
