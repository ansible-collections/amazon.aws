#!/usr/bin/env bash
set -eux

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -rf "${SCRIPT_DIR}/.collection_root"
mkdir -p "${SCRIPT_DIR}/.collection_root/ansible_collections/amazon/aws"
cp -r "${SCRIPT_DIR}/plugins" "${SCRIPT_DIR}/.collection_root/ansible_collections/amazon/aws/plugins"
cd "${SCRIPT_DIR}/.collection_root"
cp "${SCRIPT_DIR}/mypy.ini" .
mypy -p ansible_collections.amazon.aws.plugins