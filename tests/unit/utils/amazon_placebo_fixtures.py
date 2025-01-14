from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

import errno
import os

import mock
import pytest

boto3 = pytest.importorskip("boto3")
botocore = pytest.importorskip("botocore")
placebo = pytest.importorskip("placebo")

"""
Using Placebo to test modules using boto3:

This is an example test, using the placeboify fixture to test that a module
will fail if resources it depends on don't exist.

> from placebo_fixtures import placeboify, scratch_vpc
>
> def test_create_with_nonexistent_launch_config(placeboify):
>     connection = placeboify.client('autoscaling')
>     module = FakeModule('test-asg-created', None, min_size=0, max_size=0, desired_capacity=0)
>     with pytest.raises(FailJSON) as excinfo:
>         asg_module.create_autoscaling_group(connection, module)
>     .... asserts based on module state/exceptions ....
"""


@pytest.fixture(name="placeboify")
def fixture_placeboify(request, monkeypatch):
    """This fixture puts a recording/replaying harness around `boto3_conn`

    Placeboify patches the `boto3_conn` function in ec2 module_utils to return
    a boto3 session that in recording or replaying mode, depending on the
    PLACEBO_RECORD environment variable. Unset PLACEBO_RECORD (the common case
    for just running tests) will put placebo in replay mode, set PLACEBO_RECORD
    to any value to turn off replay & operate on real AWS resources.

    The recorded sessions are stored in the test file's directory, under the
    namespace `placebo_recordings/{testfile name}/{test function name}` to
    distinguish them.
    """
    session = boto3.Session(region_name="us-west-2")

    recordings_path = os.path.join(
        request.fspath.dirname,
        "placebo_recordings",
        request.fspath.basename.replace(".py", ""),
        request.function.__name__,
        # remove the test_ prefix from the function & file name
    ).replace("test_", "")

    if not os.getenv("PLACEBO_RECORD"):
        if not os.path.isdir(recordings_path):
            raise NotImplementedError(f"Missing Placebo recordings in directory: {recordings_path}")
    else:
        try:
            # make sure the directory for placebo test recordings is available
            os.makedirs(recordings_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    pill = placebo.attach(session, data_path=recordings_path)
    if os.getenv("PLACEBO_RECORD"):
        pill.record()
    else:
        pill.playback()

    def boto3_middleman_connection(module, conn_type, resource, region="us-west-2", **kwargs):
        if conn_type != "client":
            # TODO support resource-based connections
            raise ValueError(f"Mocker only supports client, not {conn_type}")
        return session.client(resource, region_name=region)

    import ansible_collections.amazon.aws.plugins.module_utils.ec2

    monkeypatch.setattr(
        ansible_collections.amazon.aws.plugins.module_utils.ec2,
        "boto3_conn",
        boto3_middleman_connection,
    )
    yield session

    # tear down
    pill.stop()


@pytest.fixture(scope="module", name="maybe_sleep")
def fixture_maybe_sleep():
    """If placebo is reading saved sessions, make sleep always take 0 seconds.

    AWS modules often perform polling or retries, but when using recorded
    sessions there's no reason to wait. We can still exercise retry and other
    code paths without waiting for wall-clock time to pass."""
    if not os.getenv("PLACEBO_RECORD"):
        p = mock.patch("time.sleep", return_value=None)
        p.start()
        yield
        p.stop()
    else:
        yield
