# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

AMAZON_AWS_COLLECTION_NAME = "amazon.aws"
AMAZON_AWS_COLLECTION_VERSION = "6.0.1"


_collection_info_context = {
    "name": AMAZON_AWS_COLLECTION_NAME,
    "version": AMAZON_AWS_COLLECTION_VERSION,
}


def set_collection_info(collection_name=None, collection_version=None):
    if collection_name:
        _collection_info_context["name"] = collection_name
    if collection_version:
        _collection_info_context["version"] = collection_version


def get_collection_info():
    return _collection_info_context
