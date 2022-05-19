# Copyright (c) 2020 Paul Arthur
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleFilterError
from ansible.module_utils.common._collections_compat import Mapping


def expand_csv_tags(mydict, separator=','):
    """Takes a dictionary and transforms it into a list of key_value strings,
        possibly after splitting the value using the supplied separator.
    
    Args:
        mydict (Mapping): The dictionary of tags to be processed.
    Raises:
        errors.AnsibleFilterError: Raised if 'mydict' is not a Mapping 
    Returns:
        A list of tags.
    """

    if not isinstance(mydict, Mapping):
        raise AnsibleFilterError("expand_csv_tags requires a dictionary, got %s instead." % type(mydict))

    ret = []

    for key in mydict:
        for val in mydict[key].split(separator):
            ret.append('{0}_{1}'.format(key, val))

    return ret


class FilterModule(object):
    def filters(self):
        return { 'expand_csv_tags': expand_csv_tags }
