# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Generic text processing utilities for AWS plugins."""

from __future__ import annotations

import re

from ansible.module_utils.common.text.converters import to_text


def filter_ansi(line: str, is_windows: bool) -> str:
    """Remove any ANSI terminal control codes and PTY artifacts.

    :param line: The input line.
    :param is_windows: Whether the output is coming from a Windows host.
    :returns: The result line.
    """
    line = to_text(line)

    # Replace PTY line wrap sequences and normalise line endings
    line = line.replace("\r\r\n", "\n")
    line = line.replace("\r\n", "\n")
    # Remove standalone carriage returns (PTY artifacts from line wrapping)
    line = line.replace("\r", "")

    if is_windows:
        osc_filter = re.compile(r"\x1b\][^\x07]*\x07")
        line = osc_filter.sub("", line)
        ansi_filter = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
        line = ansi_filter.sub("", line)

        if len(line) == 201:
            line = line[:-1]

    return line
