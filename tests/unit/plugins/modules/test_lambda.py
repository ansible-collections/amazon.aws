#
# (c) 2017 Michael De La Rue
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import pytest

from ansible_collections.community.aws.tests.unit.compat.mock import MagicMock, Mock, patch
from ansible.module_utils import basic
from ansible_collections.community.aws.tests.unit.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

boto3 = pytest.importorskip("boto3")

# lambda is a keyword so we have to hack this.
_temp = __import__('ansible_collections.community.aws.plugins.modules.lambda')
lda = getattr(_temp.community.aws.plugins.modules, "lambda")


base_lambda_config = {
    'FunctionName': 'lambda_name',
    'Role': 'arn:aws:iam::987654321012:role/lambda_basic_execution',
    'Handler': 'lambda_python.my_handler',
    'Description': 'this that the other',
    'Timeout': 3,
    'MemorySize': 128,
    'Runtime': 'python2.7',
    'CodeSha256': 'AqMZ+xptM7aC9VXu+5jyp1sqO+Nj4WFMNzQxtPMP2n8=',
    'Version': 1,
}

one_change_lambda_config = copy.copy(base_lambda_config)
one_change_lambda_config['Timeout'] = 4
two_change_lambda_config = copy.copy(one_change_lambda_config)
two_change_lambda_config['Role'] = 'arn:aws:iam::987654321012:role/lambda_advanced_execution'
code_change_lambda_config = copy.copy(base_lambda_config)
code_change_lambda_config['CodeSha256'] = 'P+Zy8U4T4RiiHWElhL10VBKj9jw4rSJ5bm/TiW+4Rts='
code_change_lambda_config['Version'] = 2

base_module_args = {
    "region": "us-west-1",
    "name": "lambda_name",
    "state": "present",
    "zip_file": "tests/unit/modules/fixtures/thezip.zip",
    "runtime": 'python2.7',
    "role": 'arn:aws:iam::987654321012:role/lambda_basic_execution',
    "memory_size": 128,
    "timeout": 3,
    "handler": 'lambda_python.my_handler'
}
one_change_module_args = copy.copy(base_module_args)
one_change_module_args['timeout'] = 4
two_change_module_args = copy.copy(one_change_module_args)
two_change_module_args['role'] = 'arn:aws:iam::987654321012:role/lambda_advanced_execution'
module_args_with_environment = dict(base_module_args, environment_variables={
    "variable_name": "variable_value"
})
delete_module_args = {
    "region": "us-west-1",
    "name": "lambda_name",
    "state": "absent",

}


@patch('ansible_collections.amazon.aws.plugins.module_utils.core.HAS_BOTO3', new=True)
@patch.object(lda.AnsibleAWSModule, 'client')
class TestLambdaModule(ModuleTestCase):
    # TODO: def test_handle_different_types_in_config_params():

    def test_create_lambda_if_not_exist(self, client_mock):
        client_mock.return_value.create_function.return_value = base_lambda_config
        get_function_after_create = {'FunctionName': 'lambda_name', 'Version': '1', 'aws_retry': True}
        client_mock.return_value.get_function.side_effect = [None, get_function_after_create]

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(base_module_args)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        client_mock.return_value.get_function.assert_called()

        client_mock.return_value.update_function_configuration.assert_not_called()
        client_mock.return_value.create_function.assert_called()

        (create_args, create_kwargs) = client_mock.return_value.create_function.call_args
        client_mock.return_value.create_function.assert_called_once_with(**create_kwargs)

    @patch.object(lda, 'sha256sum')
    def test_update_lambda_if_code_changed(self, mock_sha256sum, client_mock):
        client_mock.return_value.get_function.side_effect = [{'Configuration': base_lambda_config}, code_change_lambda_config]
        mock_sha256sum.return_value = code_change_lambda_config['CodeSha256']

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(base_module_args)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        client_mock.return_value.get_function.assert_called()
        client_mock.return_value.update_function_code.assert_called()
        client_mock.return_value.create_function.assert_not_called()

        (update_args, update_kwargs) = client_mock.return_value.update_function_code.call_args
        client_mock.return_value.update_function_code.assert_called_once_with(**update_kwargs)

    def test_update_lambda_if_config_changed(self, client_mock):
        client_mock.return_value.get_function.side_effect = [{'Configuration': base_lambda_config}, two_change_lambda_config]

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(two_change_module_args)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        client_mock.return_value.get_function.assert_called()
        client_mock.return_value.update_function_configuration.assert_called()
        client_mock.return_value.create_function.assert_not_called()

        (update_args, update_kwargs) = client_mock.return_value.update_function_configuration.call_args
        client_mock.return_value.update_function_configuration.assert_called_once_with(**update_kwargs)

    def test_update_lambda_if_only_one_config_item_changed(self, client_mock):
        client_mock.return_value.get_function.side_effect = [{'Configuration': base_lambda_config}, one_change_lambda_config]

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(one_change_module_args)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        client_mock.return_value.get_function.assert_called()
        client_mock.return_value.update_function_configuration.assert_called()
        client_mock.return_value.create_function.assert_not_called()

        (update_args, update_kwargs) = client_mock.return_value.update_function_configuration.call_args
        client_mock.return_value.update_function_configuration.assert_called_once_with(**update_kwargs)

    def test_update_lambda_if_added_environment_variable(self, client_mock):
        client_mock.return_value.get_function.side_effect = [{'Configuration': base_lambda_config}, base_lambda_config]

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(module_args_with_environment)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        client_mock.return_value.get_function.assert_called()
        client_mock.return_value.update_function_configuration.assert_called()
        client_mock.return_value.create_function.assert_not_called()

        (update_args, update_kwargs) = client_mock.return_value.update_function_configuration.call_args
        client_mock.return_value.update_function_configuration.assert_called_once_with(**update_kwargs)

        self.assertEqual(update_kwargs['Environment']['Variables'], module_args_with_environment['environment_variables'])

    def test_dont_update_lambda_if_nothing_changed(self, client_mock):
        client_mock.return_value.get_function.side_effect = [{'Configuration': base_lambda_config}, base_lambda_config]

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(base_module_args)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], False)
        client_mock.return_value.get_function.assert_called()
        client_mock.return_value.update_function_configuration.assert_not_called()
        client_mock.return_value.create_function.assert_not_called()

    def test_delete_lambda_that_exists(self, client_mock):
        client_mock.return_value.create_function.return_value = base_lambda_config
        client_mock.return_value.get_function.side_effect = [base_lambda_config, None]

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args(delete_module_args)
            lda.main()

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        client_mock.return_value.get_function.assert_called()

        client_mock.return_value.delete_function.assert_called()
        client_mock.return_value.update_function_configuration.assert_not_called()
        client_mock.return_value.create_function.assert_not_called()

        (delete_args, delete_kwargs) = client_mock.return_value.delete_function.call_args
        client_mock.return_value.delete_function.assert_called_once_with(**delete_kwargs)
