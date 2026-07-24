# (c) 2026 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_cluster_info
from ansible_collections.amazon.aws.plugins.modules.rds_cluster_info import cluster_info

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_cluster_info"


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_clusters")
def test_cluster_info_one_cluster(m_describe_db_clusters, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    cluster_id = "my-cluster"
    m_describe_db_clusters.return_value = [
        {
            "DBClusterIdentifier": cluster_id,
            "DBClusterArn": "arn:aws:rds:us-east-2:123456789012:cluster:" + cluster_id,
            "Engine": "aurora-mysql",
        }
    ]
    m_get_tags.return_value = {"Name": "my-cluster"}

    result = cluster_info(conn, module, cluster_id, filters=None)

    assert result == [
        {
            "db_cluster_identifier": cluster_id,
            "db_cluster_arn": "arn:aws:rds:us-east-2:123456789012:cluster:" + cluster_id,
            "engine": "aurora-mysql",
            "tags": {"Name": "my-cluster"},
        }
    ]
    m_describe_db_clusters.assert_called_with(conn, DBClusterIdentifier=cluster_id)
    m_get_tags.assert_called_once_with(
        conn, module, "arn:aws:rds:us-east-2:123456789012:cluster:" + cluster_id
    )


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_clusters")
def test_cluster_info_all_clusters_with_filters(m_describe_db_clusters, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    m_describe_db_clusters.return_value = [
        {
            "DBClusterIdentifier": "first-cluster",
            "DBClusterArn": "arn:aws:rds:us-east-2:123456789012:cluster:first-cluster",
            "Engine": "aurora-mysql",
        },
        {
            "DBClusterIdentifier": "second-cluster",
            "DBClusterArn": "arn:aws:rds:us-east-2:123456789012:cluster:second-cluster",
            "Engine": "aurora-mysql",
        },
    ]
    m_get_tags.return_value = {}

    result = cluster_info(conn, module, cluster_id=None, filters={"engine": "aurora-mysql"})

    assert len(result) == 2
    assert result[0]["db_cluster_identifier"] == "first-cluster"
    assert result[1]["db_cluster_identifier"] == "second-cluster"
    m_describe_db_clusters.assert_called_with(
        conn, Filters=[{"Name": "engine", "Values": ["aurora-mysql"]}]
    )
    assert m_get_tags.call_count == 2


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_clusters")
def test_cluster_info_no_results(m_describe_db_clusters, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    m_describe_db_clusters.return_value = []

    result = cluster_info(conn, module, cluster_id="nonexistent", filters=None)

    assert result == []
    m_get_tags.assert_not_called()


@patch(mod_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    rds_cluster_info.main()

    m_module.client.assert_called_with("rds")
    m_module.exit_json.assert_called_with(changed=False, clusters=[])


@patch(mod_name + ".describe_db_clusters")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_failure(m_AnsibleAWSModule, m_describe_db_clusters):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    e = AnsibleRDSError()
    m_describe_db_clusters.side_effect = e

    rds_cluster_info.main()

    m_module.client.assert_called_with("rds")
    m_module.fail_json_aws.assert_called_with(e)
