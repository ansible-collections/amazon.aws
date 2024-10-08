# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#
# Note: This code should probably live in amazon.aws rather than community.aws.
# However, for the sake of getting something into a useful shape first, it makes
# sense for it to start life in community.aws.
#

# import typing
from copy import deepcopy

try:
    import botocore.waiter as botocore_waiter

    import_error = None
except ImportError as e:
    botocore_waiter = None
    import_error = e


class BaseWaiterFactory:
    """
    A helper class used for creating additional waiters.
    Unlike the waiters available directly from botocore these waiters will
    automatically retry on common (temporary) AWS failures.

    This class should be treated as an abstract class and subclassed before use.
    A subclass should:
    - override _BaseWaiterFactory._waiter_model_data to return the data defining
      the waiter

    Usage:
    waiter_factory = BaseWaiterFactory()
    waiter = waiter_factory.get_waiter(client, 'my_waiter_name')
    waiter.wait(**params)
    """

    def __init__(self):
        if not botocore_waiter:
            return

        # While it would be nice to supliment this with the upstream data,
        # unfortunately client doesn't have a public method for getting the
        # waiter configs.
        data = self._inject_ratelimit_retries(self._waiter_model_data)
        self._model = botocore_waiter.WaiterModel(
            waiter_config=dict(version=2, waiters=data),
        )

    @property
    def _waiter_model_data(self):
        r"""
        Subclasses should override this method to return a dictionary mapping
        waiter names to the waiter definition.

        This data is similar to the data found in botocore's waiters-2.json
        files (for example: botocore/botocore/data/ec2/2016-11-15/waiters-2.json)
        with two differences:
        1) Waiter names do not have transformations applied during lookup
        2) Only the 'waiters' data is required, the data is assumed to be
           version 2

        for example:

        @property
        def _waiter_model_data(self):
            return dict(
                tgw_attachment_deleted=dict(
                    operation='DescribeTransitGatewayAttachments',
                    delay=5, maxAttempts=120,
                    acceptors=[
                        dict(state='retry', matcher='pathAll', expected='deleting', argument='TransitGatewayAttachments[].State'),
                        dict(state='success', matcher='pathAll', expected='deleted', argument='TransitGatewayAttachments[].State'),
                        dict(state='success', matcher='path', expected=True, argument='length(TransitGatewayAttachments[]) == `0`'),
                        dict(state='success', matcher='error', expected='InvalidRouteTableID.NotFound'),
                    ]
                ),
            )

        or

        @property
        def _waiter_model_data(self):
            return {
                "instance_exists": {
                    "delay": 5,
                    "maxAttempts": 40,
                    "operation": "DescribeInstances",
                    "acceptors": [
                        {
                            "matcher": "path",
                            "expected": true,
                            "argument": "length(Reservations[]) > `0`",
                            "state": "success"
                        },
                        {
                            "matcher": "error",
                            "expected": "InvalidInstanceID.NotFound",
                            "state": "retry"
                        }
                    ]
                },
            }
        """

        return dict()

    def _inject_ratelimit_retries(self, model_data):
        extra_retries = [
            "RequestLimitExceeded",
            "Unavailable",
            "ServiceUnavailable",
            "InternalFailure",
            "InternalError",
            "TooManyRequestsException",
            "Throttling",
        ]

        acceptors = []
        for error in extra_retries:
            acceptors.append(dict(state="retry", matcher="error", expected=error))

        _model_data = deepcopy(model_data)
        for waiter_name in _model_data:
            _model_data[waiter_name]["acceptors"].extend(acceptors)

        return _model_data

    def get_waiter(self, client, waiter_name: str):
        if import_error:
            # We shouldn't get here, but if someone's trying to use this without botocore installed
            # let's re-raise the actual import error
            raise import_error

        waiters = self._model.waiter_names
        if waiter_name not in waiters:
            raise NotImplementedError(f"Unable to find waiter {waiter_name}.  Available_waiters: {waiters}")
        return botocore_waiter.create_waiter_with_client(
            waiter_name,
            self._model,
            client,
        )


def custom_waiter_config(timeout: int, default_pause: int = 2):
    """
    Generates the waiter_config dict that allows configuring a custom wait_timeout

    Where the pause and the timeouts aren't perfectly divisible, this will default to waiting
    slightly longer than the configured timeout so that we give at least the timeout time for a
    change to happen.
    """

    pause = default_pause

    # Do something sensible when the user's passed a short timeout, but our default pause wouldn't
    # have allowed any retries
    if timeout < (default_pause * 3):
        pause = max(1, timeout // 3)

    attempts = 1 + (timeout // pause)

    if (attempts - 1) * pause < timeout:
        attempts += 1

    return dict(Delay=pause, MaxAttempts=attempts)
