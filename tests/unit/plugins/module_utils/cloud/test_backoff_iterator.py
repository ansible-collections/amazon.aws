# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.cloud import BackoffIterator


def test_backoff_value_generator():
    max_delay = 60
    initial = 3
    backoff = 2

    min_sleep = initial
    counter = 0
    for sleep in BackoffIterator(delay=initial, backoff=backoff, max_delay=max_delay):
        if counter > 4:
            assert sleep == max_delay
        else:
            assert sleep == min_sleep
            min_sleep *= backoff
        counter += 1
        if counter == 10:
            break


def test_backoff_value_generator_with_jitter():
    max_delay = 60
    initial = 3
    backoff = 2

    min_sleep = initial
    counter = 0
    for sleep in BackoffIterator(delay=initial, backoff=backoff, max_delay=max_delay, jitter=True):
        if counter > 4:
            assert sleep <= max_delay
        else:
            assert sleep <= min_sleep
            min_sleep *= backoff
        counter += 1
        if counter == 10:
            break
