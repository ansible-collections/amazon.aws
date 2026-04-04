# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory


class ELBWaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = dict(
            instance_deregistered=dict(
                operation="DescribeInstanceHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        expected="OutOfService",
                        argument="InstanceStates[].State",
                    ),
                    dict(
                        state="success",
                        matcher="error",
                        expected="InvalidInstance",
                    ),
                ],
            ),
            instance_in_service=dict(
                operation="DescribeInstanceHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        expected="InService",
                        argument="InstanceStates[].State",
                    ),
                    dict(
                        state="retry",
                        matcher="error",
                        expected="InvalidInstance",
                    ),
                ],
            ),
            any_instance_in_service=dict(
                operation="DescribeInstanceHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAny",
                        expected="InService",
                        argument="InstanceStates[].State",
                    ),
                ],
            ),
        )

        return data


waiter_factory = ELBWaiterFactory()
