#!/usr/bin/env bash

set -o pipefail -eux

if [ "${BASE_BRANCH:-}" ]; then
    base_branch="origin/${BASE_BRANCH}"
else
    base_branch=""
fi

# shellcheck disable=SC2086
ansible-test sanity --color -v --junit ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --docker --base-branch "${base_branch}" \
    --allow-disabled
