# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

from ._elb import waiters as _elb_waiters

if typing.TYPE_CHECKING:
    from typing import Any

    from .botocore import ClientType


def get_elb_waiter(client: ClientType, waiter_name: str) -> Any:
    """
    Get a classic ELB waiter by name.

    Args:
        client: boto3 elb client
        waiter_name: Name of the waiter to retrieve

    Returns:
        Waiter instance
    """
    return _elb_waiters.waiter_factory.get_waiter(client, waiter_name)
