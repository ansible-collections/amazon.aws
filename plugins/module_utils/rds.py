# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# It would be nice to be able to use rds.XYZ, but we're bound by Ansible's "empty-init"
# policy: https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/empty-init.html

from ._rds import api as _api
from ._rds import common as _common
from ._rds import tags as _tags
from ._rds import transformations as _transformations
from ._rds import waiters as _waiters

# common.py re-exports
AnsibleRDSError = _common.AnsibleRDSError
RDSErrorHandler = _common.RDSErrorHandler
Boto3ClientMethod = _common.Boto3ClientMethod
get_rds_method_attribute = _common.get_rds_method_attribute

# api.py re-exports
describe_db_cluster_snapshots = _api.describe_db_cluster_snapshots
describe_db_instances = _api.describe_db_instances
describe_db_snapshots = _api.describe_db_snapshots
list_tags_for_resource = _api.list_tags_for_resource
get_final_identifier = _api.get_final_identifier
handle_errors = _api.handle_errors
call_method = _api.call_method
get_snapshot = _api.get_snapshot
update_iam_roles = _api.update_iam_roles
describe_db_cluster_parameter_groups = _api.describe_db_cluster_parameter_groups
describe_db_instance_parameter_groups = _api.describe_db_instance_parameter_groups
describe_db_cluster_parameters = _api.describe_db_cluster_parameters

# waiters.py re-exports
wait_for_instance_status = _waiters.wait_for_instance_status
wait_for_cluster_status = _waiters.wait_for_cluster_status
wait_for_instance_snapshot_status = _waiters.wait_for_instance_snapshot_status
wait_for_cluster_snapshot_status = _waiters.wait_for_cluster_snapshot_status
wait_for_status = _waiters.wait_for_status

# tags.py re-exports
get_tags = _tags.get_tags
ensure_tags = _tags.ensure_tags

# transformations.py re-exports
arg_spec_to_rds_params = _transformations.arg_spec_to_rds_params
format_rds_client_method_parameters = _transformations.format_rds_client_method_parameters
compare_iam_roles = _transformations.compare_iam_roles
