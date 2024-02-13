#
# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import random
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import call

import pytest
from botocore.exceptions import ClientError

from ansible.errors import AnsibleLookupError

# from ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret import AnsibleLookupError
from ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret import LookupModule


@pytest.fixture
def lookup_plugin():
    lookup = LookupModule()
    lookup.params = {}

    lookup.get_option = MagicMock()

    def _get_option(x):
        return lookup.params.get(x)

    lookup.get_option.side_effect = _get_option
    lookup.client = MagicMock()

    return lookup


def pick_from_list(elements=None):
    if elements is None:
        elements = ["error", "warn", "skip"]
    return random.choice(elements)


def _raise_boto_clienterror(code, msg):
    params = {
        "Error": {"Code": code, "Message": msg},
        "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
    }
    return ClientError(params, "get_secret_value")


class TestLookupModuleRun:
    @pytest.mark.parametrize(
        "params,err",
        [
            ({"on_missing": "test"}, '"on_missing" must be a string and one of "error", "warn" or "skip", not test'),
            ({"on_denied": "return"}, '"on_denied" must be a string and one of "error", "warn" or "skip", not return'),
            (
                {"on_deleted": "delete"},
                '"on_deleted" must be a string and one of "error", "warn" or "skip", not delete',
            ),
            (
                {"on_missing": ["warn"]},
                '"on_missing" must be a string and one of "error", "warn" or "skip", not [\'warn\']',
            ),
            ({"on_denied": True}, '"on_denied" must be a string and one of "error", "warn" or "skip", not True'),
            (
                {"on_deleted": {"error": True}},
                '"on_deleted" must be a string and one of "error", "warn" or "skip", not {\'error\': True}',
            ),
        ],
    )
    def test_run_invalid_parameters(self, lookup_plugin, mocker, params, err):
        aws_lookup_base_run = mocker.patch(
            "ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret.AWSLookupBase.run"
        )
        aws_lookup_base_run.return_value = True
        m_list_secrets = mocker.patch(
            "ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret._list_secrets"
        )
        m_list_secrets.return_value = {"SecretList": []}

        lookup_plugin.params = params
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.run(terms=["testing_secret"], variables=[])
        assert err == str(exc_info.value)

    def test_run_by_path(self, lookup_plugin, mocker):
        aws_lookup_base_run = mocker.patch(
            "ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret.AWSLookupBase.run"
        )
        aws_lookup_base_run.return_value = True
        m_list_secrets = mocker.patch(
            "ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret._list_secrets"
        )
        secrets_lists = [{"Name": "secret-0"}, {"Name": "secret-1"}, {"Name": "secret-2"}]
        m_list_secrets.return_value = [{"SecretList": secrets_lists}]

        params = {
            "on_missing": pick_from_list(),
            "on_denied": pick_from_list(),
            "on_deleted": pick_from_list(),
            "bypath": True,
        }
        lookup_plugin.params = params

        lookup_plugin.get_secret_value = MagicMock()
        secrets_values = {
            "secret-0": "value-0",
            "secret-1": "value-1",
            "secret-2": "value-2",
        }
        lookup_plugin.get_secret_value.side_effect = lambda x, client, **kwargs: secrets_values.get(x)

        secretsmanager_client = MagicMock()
        lookup_plugin.client.return_value = secretsmanager_client

        term = "term0"
        assert [secrets_values] == lookup_plugin.run(terms=[term], variables=[])

        m_list_secrets.assert_called_once_with(secretsmanager_client, term)
        lookup_plugin.client.assert_called_once_with("secretsmanager", ANY)
        lookup_plugin.get_secret_value.assert_has_calls(
            [
                call(
                    "secret-0",
                    secretsmanager_client,
                    on_missing=params.get("on_missing"),
                    on_denied=params.get("on_denied"),
                ),
                call(
                    "secret-1",
                    secretsmanager_client,
                    on_missing=params.get("on_missing"),
                    on_denied=params.get("on_denied"),
                ),
                call(
                    "secret-2",
                    secretsmanager_client,
                    on_missing=params.get("on_missing"),
                    on_denied=params.get("on_denied"),
                ),
            ]
        )

    @pytest.mark.parametrize("join_secrets", [True, False])
    @pytest.mark.parametrize(
        "terms", [["secret-0"], ["secret-0", "secret-1"], ["secret-0", "secret-1", "secret-0", "secret-2"]]
    )
    def test_run(self, lookup_plugin, mocker, join_secrets, terms):
        aws_lookup_base_run = mocker.patch(
            "ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret.AWSLookupBase.run"
        )
        aws_lookup_base_run.return_value = True

        params = {
            "on_missing": pick_from_list(),
            "on_denied": pick_from_list(),
            "on_deleted": pick_from_list(),
            "bypath": False,
            "version_stage": MagicMock(),
            "version_id": MagicMock(),
            "nested": pick_from_list([True, False]),
            "join": join_secrets,
        }
        lookup_plugin.params = params

        lookup_plugin.get_secret_value = MagicMock()
        secrets_values = {
            "secret-0": "value-0",
            "secret-1": "value-1",
        }
        lookup_plugin.get_secret_value.side_effect = lambda x, client, **kwargs: secrets_values.get(x)

        secretsmanager_client = MagicMock()
        lookup_plugin.client.return_value = secretsmanager_client

        expected_secrets = [secrets_values.get(x) for x in terms if secrets_values.get(x) is not None]
        if join_secrets:
            expected_secrets = ["".join(expected_secrets)]

        assert expected_secrets == lookup_plugin.run(terms=terms, variables=[])

        lookup_plugin.client.assert_called_once_with("secretsmanager", ANY)
        lookup_plugin.get_secret_value.assert_has_calls(
            [
                call(
                    x,
                    secretsmanager_client,
                    version_stage=params.get("version_stage"),
                    version_id=params.get("version_id"),
                    on_missing=params.get("on_missing"),
                    on_denied=params.get("on_denied"),
                    on_deleted=params.get("on_deleted"),
                    nested=params.get("nested"),
                )
                for x in terms
            ]
        )


class TestLookupModuleGetSecretValue:
    def test_get_secret__invalid_nested_value(self, lookup_plugin):
        params = {
            "version_stage": MagicMock(),
            "version_id": MagicMock(),
            "on_missing": None,
            "on_denied": None,
            "on_deleted": None,
        }
        with pytest.raises(AnsibleLookupError) as exc_info:
            client = MagicMock()
            lookup_plugin.get_secret_value("aws_invalid_nested_secret", client, nested=True, **params)
        assert "Nested query must use the following syntax: `aws_secret_name.<key_name>.<key_name>" == str(
            exc_info.value
        )

    @pytest.mark.parametrize("versionId", [None, MagicMock()])
    @pytest.mark.parametrize("versionStage", [None, MagicMock()])
    @pytest.mark.parametrize(
        "term,nested,secretId",
        [
            ("secret0", False, "secret0"),
            ("secret0.child", False, "secret0.child"),
            ("secret0.child", True, "secret0"),
            ("secret0.root.child", False, "secret0.root.child"),
            ("secret0.root.child", True, "secret0"),
        ],
    )
    def test_get_secret__binary_secret(self, lookup_plugin, versionId, versionStage, term, nested, secretId):
        params = {
            "version_stage": versionStage,
            "version_id": versionId,
            "on_missing": None,
            "on_denied": None,
            "on_deleted": None,
        }

        client = MagicMock()
        client.get_secret_value = MagicMock()
        bin_secret_value = b"binary_value"
        client.get_secret_value.return_value = {"SecretBinary": bin_secret_value}

        assert bin_secret_value == lookup_plugin.get_secret_value(term, client, nested=nested, **params)
        api_params = {"SecretId": secretId}
        if versionId is not None:
            api_params["VersionId"] = versionId
        if versionStage:
            api_params["VersionStage"] = versionStage
        client.get_secret_value.assert_called_once_with(aws_retry=True, **api_params)

    @pytest.mark.parametrize("on_missing", ["warn", "error"])
    @pytest.mark.parametrize(
        "term,missing_key",
        [
            ("secret_name.root.child1", "root.child1"),
            ("secret_name.root.child1.nested", "root.child1"),
            ("secret_name.root.child.nested1", "root.child.nested1"),
            ("secret_name.root.child.nested.value", "root.child.nested.value"),
        ],
    )
    def test_get_secret__missing_nested_secret(self, lookup_plugin, on_missing, term, missing_key):
        client = MagicMock()
        client.get_secret_value = MagicMock()
        json_secret = '{"root": {"child": {"nested": "ansible-test-secret-0"}}}'
        client.get_secret_value.return_value = {"SecretString": json_secret}

        if on_missing == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin.get_secret_value(term, client, nested=True, on_missing=on_missing)
            assert f"Successfully retrieved secret but there exists no key {missing_key} in the secret" == str(
                exc_info.value
            )
        else:
            lookup_plugin._display = MagicMock()
            lookup_plugin._display.warning = MagicMock()
            assert lookup_plugin.get_secret_value(term, client, nested=True, on_missing=on_missing) is None
            lookup_plugin._display.warning.assert_called_once_with(
                f"Skipping, Successfully retrieved secret but there exists no key {missing_key} in the secret"
            )

    def test_get_secret__missing_secret(self, lookup_plugin):
        client = MagicMock()
        client.get_secret_value = MagicMock()
        client.get_secret_value.side_effect = _raise_boto_clienterror("UnexpecteError", "unable to retrieve Secret")

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.get_secret_value(MagicMock(), client)
        assert (
            "Failed to retrieve secret: An error occurred (UnexpecteError) when calling the get_secret_value operation: unable to retrieve Secret"
            == str(exc_info.value)
        )

    @pytest.mark.parametrize("on_denied", ["warn", "error"])
    def test_get_secret__on_denied(self, lookup_plugin, on_denied):
        client = MagicMock()
        client.get_secret_value = MagicMock()
        client.get_secret_value.side_effect = _raise_boto_clienterror(
            "AccessDeniedException", "Access denied to Secret"
        )
        term = "ansible-test-secret-0123"

        if on_denied == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin.get_secret_value(term, client, on_denied=on_denied)
            assert f"Failed to access secret {term} (AccessDenied)" == str(exc_info.value)
        else:
            lookup_plugin._display = MagicMock()
            lookup_plugin._display.warning = MagicMock()
            assert lookup_plugin.get_secret_value(term, client, on_denied=on_denied) is None
            lookup_plugin._display.warning.assert_called_once_with(f"Skipping, access denied for secret {term}")

    @pytest.mark.parametrize("on_missing", ["warn", "error"])
    def test_get_secret__on_missing(self, lookup_plugin, on_missing):
        client = MagicMock()
        client.get_secret_value = MagicMock()
        client.get_secret_value.side_effect = _raise_boto_clienterror("ResourceNotFoundException", "secret not found")
        term = "ansible-test-secret-4561"

        if on_missing == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin.get_secret_value(term, client, on_missing=on_missing)
            assert f"Failed to find secret {term} (ResourceNotFound)" == str(exc_info.value)
        else:
            lookup_plugin._display = MagicMock()
            lookup_plugin._display.warning = MagicMock()
            assert lookup_plugin.get_secret_value(term, client, on_missing=on_missing) is None
            lookup_plugin._display.warning.assert_called_once_with(f"Skipping, did not find secret {term}")

    @pytest.mark.parametrize("on_deleted", ["warn", "error"])
    def test_get_secret__on_deleted(self, lookup_plugin, on_deleted):
        client = MagicMock()
        client.get_secret_value = MagicMock()
        client.get_secret_value.side_effect = _raise_boto_clienterror(
            "ResourceMarkedForDeletion", "marked for deletion"
        )
        term = "ansible-test-secret-8790"

        if on_deleted == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin.get_secret_value(term, client, on_deleted=on_deleted)
            assert f"Failed to find secret {term} (marked for deletion)" == str(exc_info.value)
        else:
            lookup_plugin._display = MagicMock()
            lookup_plugin._display.warning = MagicMock()
            assert lookup_plugin.get_secret_value(term, client, on_deleted=on_deleted) is None
            lookup_plugin._display.warning.assert_called_once_with(
                f"Skipping, did not find secret (marked for deletion) {term}"
            )
