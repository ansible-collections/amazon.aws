# (c) 2026 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

module_name = "ansible_collections.amazon.aws.plugins.modules.route53_zone"


class TestWaitForDnssecChange:
    """Test the wait_for_dnssec_change function"""

    @patch(f"{module_name}.get_waiter")
    def test_wait_enabled(self, mock_get_waiter):
        """Test waiter is called when wait=True"""
        # Import the module to get access to the module variable
        from ansible_collections.amazon.aws.plugins.modules import route53_zone

        # Mock the module params
        route53_zone.module = MagicMock()
        route53_zone.module.params.get.side_effect = {
            "wait": True,
            "wait_timeout": 300,
        }.get

        # Mock the client and waiter
        route53_zone.client = MagicMock()
        mock_waiter = MagicMock()
        mock_get_waiter.return_value = mock_waiter

        # Call the function
        change_id = "/change/C1234567890ABC"
        route53_zone.wait_for_dnssec_change(change_id)

        # Verify waiter was called with correct parameters
        mock_get_waiter.assert_called_once_with(route53_zone.client, "resource_record_sets_changed")
        mock_waiter.wait.assert_called_once_with(
            Id=change_id,
            WaiterConfig=dict(
                Delay=5,
                MaxAttempts=60,  # 300 // 5
            ),
        )

    @patch(f"{module_name}.get_waiter")
    def test_wait_disabled(self, mock_get_waiter):
        """Test waiter is NOT called when wait=False"""
        from ansible_collections.amazon.aws.plugins.modules import route53_zone

        # Mock the module params with wait=False
        route53_zone.module = MagicMock()
        route53_zone.module.params.get.side_effect = {
            "wait": False,
            "wait_timeout": 300,
        }.get

        # Call the function
        change_id = "/change/C1234567890ABC"
        route53_zone.wait_for_dnssec_change(change_id)

        # Verify waiter was NOT called
        mock_get_waiter.assert_not_called()

    @patch(f"{module_name}.get_waiter")
    def test_wait_timeout_calculation(self, mock_get_waiter):
        """Test timeout is correctly calculated"""
        from ansible_collections.amazon.aws.plugins.modules import route53_zone

        # Mock the module params with custom timeout
        route53_zone.module = MagicMock()
        route53_zone.module.params.get.side_effect = {
            "wait": True,
            "wait_timeout": 600,  # 10 minutes
        }.get

        route53_zone.client = MagicMock()
        mock_waiter = MagicMock()
        mock_get_waiter.return_value = mock_waiter

        # Call the function
        change_id = "/change/C1234567890ABC"
        route53_zone.wait_for_dnssec_change(change_id)

        # Verify MaxAttempts is 600 // 5 = 120
        mock_waiter.wait.assert_called_once_with(
            Id=change_id,
            WaiterConfig=dict(
                Delay=5,
                MaxAttempts=120,  # 600 // 5
            ),
        )

    @patch(f"{module_name}.get_waiter")
    def test_wait_waiter_error(self, mock_get_waiter):
        """Test WaiterError is handled correctly"""
        from botocore.exceptions import WaiterError

        from ansible_collections.amazon.aws.plugins.modules import route53_zone

        # Mock the module params
        route53_zone.module = MagicMock()
        route53_zone.module.params.get.side_effect = {
            "wait": True,
            "wait_timeout": 300,
        }.get

        route53_zone.client = MagicMock()
        mock_waiter = MagicMock()
        mock_get_waiter.return_value = mock_waiter

        # Make waiter raise WaiterError
        waiter_error = WaiterError(
            name="resource_record_sets_changed",
            reason="Max attempts exceeded",
            last_response={},
        )
        mock_waiter.wait.side_effect = waiter_error

        # Call the function
        change_id = "/change/C1234567890ABC"
        route53_zone.wait_for_dnssec_change(change_id)

        # Verify fail_json_aws was called
        route53_zone.module.fail_json_aws.assert_called_once_with(
            waiter_error, msg="Timeout waiting for DNSSEC changes to be replicated"
        )


class TestEnsureDnssec:
    """Test the ensure_dnssec function with wait support"""

    @patch(f"{module_name}.wait_for_dnssec_change")
    @patch(f"{module_name}.enable_hosted_zone_dnssec")
    @patch(f"{module_name}.get_dnssec")
    def test_enable_dnssec_with_wait(self, mock_get_dnssec, mock_enable_dnssec, mock_wait):
        """Test enabling DNSSEC calls waiter when wait=True"""
        from ansible_collections.amazon.aws.plugins.modules import route53_zone

        # Mock module params
        route53_zone.module = MagicMock()
        route53_zone.module.params.get.side_effect = {
            "dnssec": True,
            "wait": True,
        }.get
        route53_zone.module.check_mode = False

        # Mock get_dnssec to return NOT_SIGNING
        mock_get_dnssec.return_value = {
            "Status": {"ServeSignature": "NOT_SIGNING"},
        }

        # Mock enable_hosted_zone_dnssec to return ChangeInfo
        mock_enable_dnssec.return_value = {
            "ChangeInfo": {
                "Id": "/change/C1234567890ABC",
                "Status": "PENDING",
            }
        }

        # Call the function
        zone_id = "Z1234567890ABC"
        changed = route53_zone.ensure_dnssec(zone_id)

        # Verify enable was called
        mock_enable_dnssec.assert_called_once_with(zone_id)

        # Verify waiter was called with the change ID
        mock_wait.assert_called_once_with("/change/C1234567890ABC")

        # Verify changed is True
        assert changed is True

    @patch(f"{module_name}.wait_for_dnssec_change")
    @patch(f"{module_name}.disable_hosted_zone_dnssec")
    @patch(f"{module_name}.get_dnssec")
    def test_disable_dnssec_with_wait(self, mock_get_dnssec, mock_disable_dnssec, mock_wait):
        """Test disabling DNSSEC calls waiter when wait=True"""
        from ansible_collections.amazon.aws.plugins.modules import route53_zone

        # Mock module params
        route53_zone.module = MagicMock()
        route53_zone.module.params.get.side_effect = {
            "dnssec": False,
            "wait": True,
        }.get
        route53_zone.module.check_mode = False

        # Mock get_dnssec to return SIGNING
        mock_get_dnssec.return_value = {
            "Status": {"ServeSignature": "SIGNING"},
        }

        # Mock disable_hosted_zone_dnssec to return ChangeInfo
        mock_disable_dnssec.return_value = {
            "ChangeInfo": {
                "Id": "/change/C9876543210ABC",
                "Status": "PENDING",
            }
        }

        # Call the function
        zone_id = "Z1234567890ABC"
        changed = route53_zone.ensure_dnssec(zone_id)

        # Verify disable was called
        mock_disable_dnssec.assert_called_once_with(zone_id)

        # Verify waiter was called with the change ID
        mock_wait.assert_called_once_with("/change/C9876543210ABC")

        # Verify changed is True
        assert changed is True
