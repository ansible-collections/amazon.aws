# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory


class S3WaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        PATH_BUCKET_KEY_ENABLED = "ServerSideEncryptionConfiguration.Rules[].BucketKeyEnabled"
        data = dict(
            bucket_exists=dict(
                operation="HeadBucket",
                delay=5,
                maxAttempts=20,
                acceptors=[
                    dict(state="success", matcher="status", expected=200),
                    dict(state="success", matcher="status", expected=301),
                    dict(state="success", matcher="status", expected=403),
                ],
            ),
            bucket_not_exists=dict(
                operation="HeadBucket",
                delay=5,
                maxAttempts=60,
                acceptors=[
                    dict(state="success", matcher="status", expected=404),
                ],
            ),
            bucket_versioning_enabled=dict(
                operation="GetBucketVersioning",
                delay=8,
                maxAttempts=25,
                acceptors=[
                    dict(state="success", matcher="path", argument="Status", expected="Enabled"),
                ],
            ),
            bucket_versioning_suspended=dict(
                operation="GetBucketVersioning",
                delay=8,
                maxAttempts=25,
                acceptors=[
                    dict(state="success", matcher="path", argument="Status", expected="Suspended"),
                ],
            ),
            bucket_key_encryption_enabled=dict(
                operation="GetBucketEncryption",
                delay=5,
                maxAttempts=12,
                acceptors=[
                    dict(state="success", matcher="pathAll", argument=PATH_BUCKET_KEY_ENABLED, expected=True),
                ],
            ),
            bucket_key_encryption_disabled=dict(
                operation="GetBucketEncryption",
                delay=5,
                maxAttempts=12,
                acceptors=[
                    dict(state="success", matcher="pathAll", argument=PATH_BUCKET_KEY_ENABLED, expected=False),
                ],
            ),
        )

        return data


waiter_factory = S3WaiterFactory()
