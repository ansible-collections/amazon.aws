# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2018, Will Thames <will@thames.id.au>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os

from ansible.errors import AnsibleError, AnsibleAction, AnsibleActionFail, AnsibleFileNotFound
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        """handler for s3_object operations

        This adds the magic that means 'src' can point to both a 'remote' file
        on the 'host' or in the 'files/' lookup path on the controller.
        """
        self._supports_async = True

        if task_vars is None:
            task_vars = dict()

        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        source = self._task.args.get("src", None)

        try:
            new_module_args = self._task.args.copy()
            if source:
                source = os.path.expanduser(source)

                # For backward compatibility check if the file exists on the remote; it should take precedence
                if not self._remote_file_exists(source):
                    try:
                        source = self._loader.get_real_file(self._find_needle("files", source), decrypt=False)
                        new_module_args["src"] = source
                    except AnsibleFileNotFound:
                        # module handles error message for nonexistent files
                        new_module_args["src"] = source
                    except AnsibleError as e:
                        raise AnsibleActionFail(to_text(e))

            wrap_async = self._task.async_val and not self._connection.has_native_async
            # execute the s3_object module with the updated args
            result = merge_hash(
                result, self._execute_module(module_args=new_module_args, task_vars=task_vars, wrap_async=wrap_async)
            )

            if not wrap_async:
                # remove a temporary path we created
                self._remove_tmp_path(self._connection._shell.tmpdir)

        except AnsibleAction as e:
            result.update(e.result)
        return result
