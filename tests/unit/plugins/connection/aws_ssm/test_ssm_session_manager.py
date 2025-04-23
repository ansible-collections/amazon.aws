# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# While it may seem appropriate to import our custom fixtures here, the pytest_ansible pytest plugin
# isn't as agressive as the ansible_test._util.target.pytest.plugins.ansible_pytest_collections plugin
# when it comes to rewriting the import paths and as such we can't import fixtures via their
# absolute import path or across collections.


import random
import string
import subprocess
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

from ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager import ProcessManager
from ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager import SSMProcessManagerTimeOutFailure
from ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager import SSMSessionManager

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_poll.py requires the python modules 'boto3' and 'botocore'")


def verbosity_display(verbose, message):
    print("".join(["v" for i in range(verbose)]) + " >> " + message)


@pytest.mark.parametrize(
    "timeout,number_poll_false",
    [
        (5, 2),
        (5, 4),
    ],
)
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
def test_process_manager_poll(m_create_polling_obj, timeout, number_poll_false):
    session = MagicMock()
    stdout = MagicMock()

    proc_mgr = ProcessManager(
        instance_id=MagicMock(), session=session, stdout=stdout, timeout=timeout, verbosity_display=verbosity_display
    )
    proc_mgr.poll_stdout = MagicMock()
    proc_mgr.poll_stdout.side_effect = [False for i in range(number_poll_false)] + [True]

    for result in proc_mgr.poll("UNIT_TEST", "ansible-test units"):
        if result:
            break
    m_create_polling_obj.assert_called_once_with(stdout)


@patch("time.time")
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
def test_process_manager_poll_with_timeout(m_create_polling_obj, time_time):
    session = MagicMock()
    stdout = MagicMock()

    session.poll = MagicMock()
    session.poll.side_effect = lambda: None

    time_time.side_effect = [0, 4]

    instance_id = "i-" + "".join([random.choice(string.ascii_lowercase + string.digits) for i in range(12)])
    timeout = 3
    proc_mgr = ProcessManager(
        instance_id=instance_id, session=session, stdout=stdout, timeout=timeout, verbosity_display=verbosity_display
    )
    proc_mgr.poll_stdout = MagicMock()
    proc_mgr.poll_stdout.side_effect = [False for i in range(2 * timeout)]

    with pytest.raises(SSMProcessManagerTimeOutFailure) as exc_info:
        for result in proc_mgr.poll("UNIT_TEST", "ansible-test units"):
            if result:
                break
    assert str(exc_info.value) == f"UNIT_TEST command 'ansible-test units' timeout on host: {instance_id}"
    m_create_polling_obj.assert_called_once_with(stdout)


@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
def test_process_manager_flush_stderr(m_create_polling_obj):
    session = MagicMock()
    stdout = MagicMock()

    poller = MagicMock()
    m_create_polling_obj.return_value = poller
    poller.poll.side_effect = [True, True, None]

    session.poll = MagicMock()
    session.poll.side_effect = lambda: None
    stderr = MagicMock()
    session.stderr = stderr
    session.stderr.readline.side_effect = ["This is the ", "stderr content."]

    proc_mgr = ProcessManager(
        instance_id=MagicMock(),
        session=session,
        stdout=stdout,
        timeout=MagicMock(),
        verbosity_display=verbosity_display,
    )
    assert proc_mgr.flush_stderr() == "This is the stderr content."
    m_create_polling_obj.assert_has_calls([call(stdout), call(stderr)])
    poller.poll.assert_called()


@pytest.mark.parametrize(
    "stdout_text, match",
    [
        (["This ", "has been", " found"], "This has been found"),
        (["Do not add this part", "This ", "has been", " found"], "This has been found"),
        (["ansible", " is ", "super"], lambda t: t.replace(" ", "").split("is") == ["ansible", "super"]),
    ],
)
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
def test_process_manager_wait_for_match(m_create_polling_obj, stdout_text, match):
    session = MagicMock()
    stdout = MagicMock()

    session.poll = MagicMock()
    session.poll.side_effect = lambda: None

    proc_mgr = ProcessManager(
        instance_id=MagicMock(),
        session=session,
        stdout=stdout,
        timeout=MagicMock(),
        verbosity_display=verbosity_display,
    )
    proc_mgr.poll = MagicMock()

    proc_mgr.poll.return_value = [True for i in range(5)] + [
        SSMProcessManagerTimeOutFailure("unit tests process failure")
    ]
    proc_mgr.stdout_read_text = MagicMock()
    proc_mgr.stdout_read_text.side_effect = stdout_text

    label = MagicMock()
    cmd = MagicMock()
    proc_mgr.wait_for_match(label=label, cmd=cmd, match=match)


@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
def test_process_manager_wait_for_match_failure(m_create_polling_obj):
    session = MagicMock()
    stdout = MagicMock()

    session.poll = MagicMock()
    session.poll.side_effect = lambda: None

    proc_mgr = ProcessManager(
        instance_id=MagicMock(),
        session=session,
        stdout=stdout,
        timeout=MagicMock(),
        verbosity_display=verbosity_display,
    )
    proc_mgr.poll = MagicMock()

    def _mock_poll(**kwargs):
        for i in range(5):
            yield True
        raise SSMProcessManagerTimeOutFailure("unit tests process failure")

    proc_mgr.poll.side_effect = _mock_poll
    proc_mgr.stdout_read_text = MagicMock()
    proc_mgr.stdout_read_text.side_effect = ["ansible" for i in range(20)]

    label = MagicMock()
    cmd = MagicMock()

    with pytest.raises(SSMProcessManagerTimeOutFailure) as exc_info:
        proc_mgr.wait_for_match(label=label, cmd=cmd, match="ansible is great")
    assert str(exc_info.value) == "unit tests process failure"


@pytest.mark.parametrize("has_timeout", [True, False])
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
def test_process_manager_terminate(m_create_polling_obj, has_timeout):
    session = MagicMock()
    stdout = MagicMock()

    session.poll = MagicMock()
    session.poll.side_effect = lambda: None

    proc_mgr = ProcessManager(
        instance_id=MagicMock(),
        session=session,
        stdout=stdout,
        timeout=MagicMock(),
        verbosity_display=verbosity_display,
    )
    proc_mgr.poll = MagicMock()
    proc_mgr._has_timeout = has_timeout
    proc_mgr.terminate()

    if has_timeout:
        session.terminate.assert_called_once()
        session.communicate.assert_not_called()
    else:
        session.terminate.assert_not_called()
        session.communicate.assert_called_once_with(b"\nexit\n")


class TestSSMSessionManager:
    def create_session_manager(self):
        self.ssm_client = MagicMock()
        self.instance_id = MagicMock()
        self.ssm_timeout = MagicMock()
        self.verbosity = verbosity_display

        session = SSMSessionManager(
            ssm_client=self.ssm_client,
            instance_id=self.instance_id,
            ssm_timeout=self.instance_id,
            verbosity_display=self.verbosity,
        )

        return session

    def test_terminate_no_session_id(self):
        session = self.create_session_manager()
        session._session = MagicMock()
        session.terminate()
        session._session.terminate.assert_not_called()
        session._session.communicate.assert_not_called()
        session._client.terminate_session.assert_not_called()

    def test_terminate_with_session_id(self):
        session = self.create_session_manager()
        session_id = MagicMock()
        session._session_id = session_id
        session._process_mgr = MagicMock()

        session.terminate()
        session._process_mgr.terminate.assert_called_once()
        session._client.terminate_session.assert_called_once_with(SessionId=session_id)
        assert not session._session_id

    @pytest.mark.parametrize("parameters", [None, {"Session": "Parameters"}])
    @pytest.mark.parametrize("document_name", [True, False])
    @patch("json.dumps")
    @patch("os.fdopen")
    @patch("os.close")
    @patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager.ProcessManager")
    @patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager.Popen")
    @patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager.openpty")
    @patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager.to_text")
    @patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj")
    def test_start_session(
        self,
        m_create_polling_obj,
        m_to_text,
        m_openpty,
        m_popen,
        m_process_manager,
        m_os_close,
        m_os_fdopen,
        m_json_dumps,
        parameters,
        document_name,
    ):
        m_json_dumps.side_effect = lambda x: x
        session = self.create_session_manager()
        session._client.start_session = MagicMock()
        session_id = MagicMock()
        session._client.start_session.return_value = {"SessionId": session_id}
        session._prepare_terminal = MagicMock()
        document_name = MagicMock() if document_name else None
        region_name = MagicMock()
        profile_name = MagicMock()
        executable = MagicMock()

        stdout_r = MagicMock()
        stdout_w = MagicMock()
        m_openpty.return_value = (stdout_r, stdout_w)

        p_session = MagicMock()
        m_popen.return_value = p_session

        stdout = MagicMock()
        m_os_fdopen.return_value = stdout

        session.start_session(
            executable=executable,
            document_name=document_name,
            region_name=region_name,
            profile_name=profile_name,
            parameters=parameters,
        )

        m_os_close.assert_called_once_with(stdout_w)
        m_os_fdopen.assert_called_once_with(stdout_r, "rb", 0)

        args = {"Target": session.instance_id, "Parameters": parameters or {}}
        if document_name:
            args.update({"DocumentName": document_name})
        session._client.start_session.assert_called_once_with(**args)

        m_popen.assert_called_once_with(
            [
                executable,
                {"SessionId": session_id},
                region_name,
                "StartSession",
                profile_name,
                {"Target": session.instance_id},
                session._client.meta.endpoint_url,
            ],
            stdin=subprocess.PIPE,
            stdout=stdout_w,
            stderr=subprocess.PIPE,
            close_fds=True,
            bufsize=0,
        )

        m_process_manager.assert_called_once_with(
            instance_id=session.instance_id,
            session=p_session,
            stdout=stdout,
            timeout=session._timeout,
            verbosity_display=session.verbosity_display,
        )
