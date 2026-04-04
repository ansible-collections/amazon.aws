# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ..waiter import BaseWaiterFactory


class ELBv2WaiterFactory(BaseWaiterFactory):
    @property
    def _waiter_model_data(self):
        data = dict(
            target_in_service=dict(
                operation="DescribeTargetHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="pathAll",
                        expected="healthy",
                        argument="TargetHealthDescriptions[].TargetHealth.State",
                    ),
                    dict(
                        state="retry",
                        matcher="error",
                        expected="InvalidInstance",
                    ),
                ],
            ),
            target_deregistered=dict(
                operation="DescribeTargetHealth",
                delay=15,
                maxAttempts=40,
                acceptors=[
                    dict(
                        state="success",
                        matcher="error",
                        expected="InvalidTarget",
                    ),
                    dict(
                        state="success",
                        matcher="pathAll",
                        expected="unused",
                        argument="TargetHealthDescriptions[].TargetHealth.State",
                    ),
                ],
            ),
        )

        return data


waiter_factory = ELBv2WaiterFactory()
