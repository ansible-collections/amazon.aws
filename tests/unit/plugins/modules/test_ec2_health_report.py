# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from ansible_collections.community.aws.plugins.modules import ec2_health_report


@pytest.fixture
def mock_module():
    """Create a mock AnsibleModule."""
    module = MagicMock()
    module.params = {
        'region': 'us-east-1',
        'filters': {},
        'metric_period': 300,
        'metric_duration': 1,
        'include_metrics': ['CPUUtilization', 'StatusCheckFailed'],
        'send_email': False,
        'email_config': None,
        'format': 'json'
    }
    module.check_mode = False
    module.fail_json = MagicMock(side_effect=Exception("fail_json called"))
    module.fail_json_aws = MagicMock(side_effect=Exception("fail_json_aws called"))
    module.exit_json = MagicMock()
    module.warn = MagicMock()
    return module


@pytest.fixture
def sample_instance():
    """Sample EC2 instance data."""
    return {
        'InstanceId': 'i-1234567890abcdef0',
        'InstanceType': 't3.medium',
        'State': {'Name': 'running'},
        'LaunchTime': datetime(2025, 1, 1, 12, 0, 0),
        'PrivateIpAddress': '10.0.1.25',
        'PublicIpAddress': '54.123.45.67',
        'Placement': {'AvailabilityZone': 'us-east-1a'},
        'Tags': [
            {'Key': 'Name', 'Value': 'test-instance'},
            {'Key': 'Environment', 'Value': 'production'}
        ]
    }


@pytest.fixture
def sample_cloudwatch_response():
    """Sample CloudWatch metrics response."""
    return {
        'Datapoints': [
            {'Average': 45.0, 'Maximum': 60.0, 'Minimum': 30.0, 'Timestamp': datetime.utcnow()},
            {'Average': 50.0, 'Maximum': 65.0, 'Minimum': 35.0, 'Timestamp': datetime.utcnow()},
            {'Average': 48.0, 'Maximum': 62.0, 'Minimum': 33.0, 'Timestamp': datetime.utcnow()}
        ]
    }


class TestGetEC2Instances:
    """Test get_ec2_instances function."""
    
    def test_get_instances_no_filters(self, mock_module):
        """Test getting instances without filters."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        
        mock_paginator.paginate.return_value = [
            {
                'Reservations': [
                    {'Instances': [{'InstanceId': 'i-123'}]}
                ]
            }
        ]
        
        instances = ec2_health_report.get_ec2_instances(mock_module, mock_client)
        
        assert len(instances) == 1
        assert instances[0]['InstanceId'] == 'i-123'
        mock_paginator.paginate.assert_called_once_with(Filters=[])
    
    def test_get_instances_with_filters(self, mock_module):
        """Test getting instances with filters."""
        mock_module.params['filters'] = {'instance-state-name': 'running'}
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        
        mock_paginator.paginate.return_value = [
            {
                'Reservations': [
                    {'Instances': [{'InstanceId': 'i-456', 'State': {'Name': 'running'}}]}
                ]
            }
        ]
        
        instances = ec2_health_report.get_ec2_instances(mock_module, mock_client)
        
        assert len(instances) == 1
        assert instances[0]['State']['Name'] == 'running'
    
    def test_get_instances_with_tag_filters(self, mock_module):
        """Test getting instances with tag filters."""
        mock_module.params['filters'] = {'tag:Environment': 'production'}
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        
        mock_paginator.paginate.return_value = [
            {
                'Reservations': [
                    {'Instances': [{'InstanceId': 'i-789'}]}
                ]
            }
        ]
        
        instances = ec2_health_report.get_ec2_instances(mock_module, mock_client)
        
        assert len(instances) == 1
        # Verify tag filter was converted correctly
        call_args = mock_paginator.paginate.call_args[1]['Filters']
        assert any(f['Name'] == 'tag:Environment' for f in call_args)


class TestGetCloudWatchMetrics:
    """Test get_cloudwatch_metrics function."""
    
    def test_get_metrics_success(self, mock_module, sample_cloudwatch_response):
        """Test successful metric retrieval."""
        mock_client = MagicMock()
        mock_client.get_metric_statistics.return_value = sample_cloudwatch_response
        
        result = ec2_health_report.get_cloudwatch_metrics(
            mock_module, mock_client, 'i-123', 'CPUUtilization'
        )
        
        assert result is not None
        assert 'average' in result
        assert 'maximum' in result
        assert 'minimum' in result
        assert result['datapoints'] == 3
        assert result['average'] == 47.67  # Average of 45, 50, 48
        assert result['maximum'] == 65.0
        assert result['minimum'] == 30.0
    
    def test_get_metrics_no_datapoints(self, mock_module):
        """Test metric retrieval with no datapoints."""
        mock_client = MagicMock()
        mock_client.get_metric_statistics.return_value = {'Datapoints': []}
        
        result = ec2_health_report.get_cloudwatch_metrics(
            mock_module, mock_client, 'i-123', 'CPUUtilization'
        )
        
        assert result is None
    
    def test_get_metrics_client_error(self, mock_module):
        """Test metric retrieval with client error."""
        from botocore.exceptions import ClientError
        
        mock_client = MagicMock()
        mock_client.get_metric_statistics.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'GetMetricStatistics'
        )
        
        result = ec2_health_report.get_cloudwatch_metrics(
            mock_module, mock_client, 'i-123', 'CPUUtilization'
        )
        
        assert result is None
        mock_module.warn.assert_called_once()
    
    def test_get_metrics_custom_period(self, mock_module, sample_cloudwatch_response):
        """Test metric retrieval with custom period."""
        mock_module.params['metric_period'] = 60
        mock_module.params['metric_duration'] = 24
        
        mock_client = MagicMock()
        mock_client.get_metric_statistics.return_value = sample_cloudwatch_response
        
        result = ec2_health_report.get_cloudwatch_metrics(
            mock_module, mock_client, 'i-123', 'CPUUtilization'
        )
        
        assert result is not None
        call_args = mock_client.get_metric_statistics.call_args[1]
        assert call_args['Period'] == 60


class TestCollectInstanceHealth:
    """Test collect_instance_health function."""
    
    def test_collect_health_complete(self, mock_module, sample_instance, sample_cloudwatch_response):
        """Test collecting complete health data."""
        mock_ec2_client = MagicMock()
        mock_cw_client = MagicMock()
        mock_cw_client.get_metric_statistics.return_value = sample_cloudwatch_response
        
        result = ec2_health_report.collect_instance_health(
            mock_module, mock_ec2_client, mock_cw_client, sample_instance
        )
        
        assert result['instance_id'] == 'i-1234567890abcdef0'
        assert result['instance_type'] == 't3.medium'
        assert result['state'] == 'running'
        assert result['tags']['Name'] == 'test-instance'
        assert result['tags']['Environment'] == 'production'
        assert 'metrics' in result
        assert len(result['metrics']) == 2  # CPUUtilization and StatusCheckFailed
    
    def test_collect_health_no_public_ip(self, mock_module, sample_instance, sample_cloudwatch_response):
        """Test collecting health data for instance without public IP."""
        del sample_instance['PublicIpAddress']
        
        mock_ec2_client = MagicMock()
        mock_cw_client = MagicMock()
        mock_cw_client.get_metric_statistics.return_value = sample_cloudwatch_response
        
        result = ec2_health_report.collect_instance_health(
            mock_module, mock_ec2_client, mock_cw_client, sample_instance
        )
        
        assert result['public_ip'] == 'N/A'
    
    def test_collect_health_no_tags(self, mock_module, sample_instance, sample_cloudwatch_response):
        """Test collecting health data for instance without tags."""
        del sample_instance['Tags']
        
        mock_ec2_client = MagicMock()
        mock_cw_client = MagicMock()
        mock_cw_client.get_metric_statistics.return_value = sample_cloudwatch_response
        
        result = ec2_health_report.collect_instance_health(
            mock_module, mock_ec2_client, mock_cw_client, sample_instance
        )
        
        assert result['tags'] == {}


class TestFormatReportText:
    """Test format_report_text function."""
    
    def test_format_text_basic(self):
        """Test basic text formatting."""
        report_data = {
            'timestamp': '2025-11-13T10:00:00Z',
            'region': 'us-east-1',
            'instance_count': 1,
            'instances': [
                {
                    'instance_id': 'i-123',
                    'instance_type': 't3.medium',
                    'state': 'running',
                    'private_ip': '10.0.1.1',
                    'public_ip': '54.1.2.3',
                    'launch_time': '2025-01-01T12:00:00',
                    'tags': {'Name': 'test'},
                    'metrics': {
                        'CPUUtilization': {'average': 45.5, 'maximum': 60.0, 'minimum': 30.0}
                    }
                }
            ]
        }
        
        result = ec2_health_report.format_report_text(report_data)
        
        assert 'AWS EC2 HEALTH REPORT' in result
        assert 'us-east-1' in result
        assert 'i-123' in result
        assert 't3.medium' in result
        assert 'CPUUtilization' in result


class TestFormatReportHTML:
    """Test format_report_html function."""
    
    def test_format_html_basic(self):
        """Test basic HTML formatting."""
        report_data = {
            'timestamp': '2025-11-13T10:00:00Z',
            'region': 'us-east-1',
            'instance_count': 1,
            'instances': [
                {
                    'instance_id': 'i-123',
                    'instance_type': 't3.medium',
                    'state': 'running',
                    'private_ip': '10.0.1.1',
                    'public_ip': '54.1.2.3',
                    'launch_time': '2025-01-01T12:00:00',
                    'tags': {'Name': 'test'},
                    'metrics': {
                        'CPUUtilization': {'average': 45.5, 'maximum': 60.0, 'minimum': 30.0}
                    }
                }
            ]
        }
        
        result = ec2_health_report.format_report_html(report_data)
        
        assert '<html>' in result
        assert '<table>' in result
        assert 'i-123' in result
        assert 't3.medium' in result
        assert 'CPUUtilization' in result
        assert '</html>' in result
    
    def test_format_html_cpu_classes(self):
        """Test HTML formatting with CPU classes."""
        report_data = {
            'timestamp': '2025-11-13T10:00:00Z',
            'region': 'us-east-1',
            'instance_count': 3,
            'instances': [
                {
                    'instance_id': 'i-low',
                    'tags': {},
                    'instance_type': 't3.micro',
                    'state': 'running',
                    'private_ip': '10.0.1.1',
                    'public_ip': 'N/A',
                    'metrics': {'CPUUtilization': {'average': 30.0, 'maximum': 40.0, 'minimum': 20.0}}
                },
                {
                    'instance_id': 'i-medium',
                    'tags': {},
                    'instance_type': 't3.medium',
                    'state': 'running',
                    'private_ip': '10.0.1.2',
                    'public_ip': 'N/A',
                    'metrics': {'CPUUtilization': {'average': 70.0, 'maximum': 80.0, 'minimum': 60.0}}
                },
                {
                    'instance_id': 'i-high',
                    'tags': {},
                    'instance_type': 't3.large',
                    'state': 'running',
                    'private_ip': '10.0.1.3',
                    'public_ip': 'N/A',
                    'metrics': {'CPUUtilization': {'average': 90.0, 'maximum': 95.0, 'minimum': 85.0}}
                }
            ]
        }
        
        result = ec2_health_report.format_report_html(report_data)
        
        assert 'healthy' in result
        assert 'warning' in result
        assert 'critical' in result


class TestSendEmailReport:
    """Test send_email_report function."""
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, mock_module):
        """Test successful email sending."""
        mock_module.params['email_config'] = {
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_username': 'user@example.com',
            'smtp_password': 'password',
            'from_addr': 'sender@example.com',
            'to_addrs': ['recipient@example.com'],
            'subject': 'Test Report',
            'use_tls': True
        }
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = ec2_health_report.send_email_report(
            mock_module, "Test content", "text"
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_no_tls(self, mock_smtp, mock_module):
        """Test email sending without TLS."""
        mock_module.params['email_config'] = {
            'smtp_host': 'smtp.example.com',
            'smtp_port': 25,
            'smtp_username': 'user@example.com',
            'smtp_password': 'password',
            'from_addr': 'sender@example.com',
            'to_addrs': ['recipient@example.com'],
            'subject': 'Test Report',
            'use_tls': False
        }
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = ec2_health_report.send_email_report(
            mock_module, "Test content", "text"
        )
        
        assert result is True
        mock_server.starttls.assert_not_called()


class TestMainFunction:
    """Test main function."""
    
    @patch('ansible_collections.community.aws.plugins.modules.ec2_health_report.AnsibleAWSModule')
    def test_main_check_mode(self, mock_ansible_module):
        """Test main function in check mode."""
        mock_module_instance = MagicMock()
        mock_module_instance.check_mode = True
        mock_ansible_module.return_value = mock_module_instance
        
        ec2_health_report.main()
        
        mock_module_instance.exit_json.assert_called_once()
        call_args = mock_module_instance.exit_json.call_args[1]
        assert call_args['changed'] is False
