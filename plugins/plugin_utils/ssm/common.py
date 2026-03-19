# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from typing import TypedDict

# Length of random marker strings used for output parsing
MARK_LENGTH = 26

# Exit code returned when S3 download fails in Windows executor error handler
S3_DOWNLOAD_ERROR_EXIT_CODE = 99


class CommandResult(TypedDict):
    """
    A dictionary that contains the executed command results.
    """

    returncode: int
    stdout: str
    stderr: str
