# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Generic iterator utilities for chunking data."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Iterator

from ansible.module_utils._text import to_bytes


def chunks(lst: list, n: int) -> Iterator[list[Any]]:
    """
    Yield successive n-sized chunks from a list.

    :param lst: The list to chunk.
    :param n: The size of each chunk.
    :returns: Iterator yielding list chunks of size n.
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def chunked_payload(payload: bytes | str, buffer_size: int = 1024) -> Iterator[tuple[bytes, bool]]:
    """
    Yield successive buffer-sized chunks from payload with completion flag.

    Useful for streaming data in fixed-size chunks, with each chunk accompanied
    by a flag indicating whether it's the last chunk.

    :param payload: The data to chunk (bytes or string)
    :param buffer_size: Size of each chunk in bytes (default: 1024)
    :returns: Iterator yielding tuples of (chunk_bytes, is_last_chunk)
    """
    payload_bytes = to_bytes(payload)
    byte_count = len(payload_bytes)
    for i in range(0, byte_count, buffer_size):
        yield payload_bytes[i : i + buffer_size], i + buffer_size >= byte_count
