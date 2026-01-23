import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import crytonix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import HealthToolbox, NetworkToolbox

class TestHealthToolbox:
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        assert "Posture Check" in result
        assert isinstance(result, str)

    def test_stretch_exercise(self):
        result = HealthToolbox.stretch_exercise()
        assert "Stretch Time" in result
        assert isinstance(result, str)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        assert "💧" in result or "Water" in result
        assert isinstance(result, str)

    def test_take_break(self):
        result = HealthToolbox.take_break()
        assert "Break Time" in result
        assert isinstance(result, str)

class TestNetworkToolbox:
    @patch('subprocess.run')
    def test_ping_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Reply from 127.0.0.1: bytes=32 time<1ms TTL=128"
        mock_run.return_value = mock_result

        result = NetworkToolbox.ping("localhost")
        assert "Ping success" in result
        assert "Reply from" in result

        # Verify shell=False
        args, kwargs = mock_run.call_args
        assert kwargs.get('shell') is False
        assert isinstance(args[0], list)

    @patch('subprocess.run')
    def test_ping_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Request timed out."
        mock_run.return_value = mock_result

        result = NetworkToolbox.ping("invalid-host")
        assert "Ping failed" in result

    def test_ping_injection_prevention(self):
        result = NetworkToolbox.ping("localhost; rm -rf /")
        assert "Error: Invalid host format" in result

    @patch('socket.socket')
    def test_check_port_open(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_socket_cls.return_value.__enter__.return_value = mock_socket

        result = NetworkToolbox.check_port("localhost", 80)
        assert "is OPEN" in result

    @patch('socket.socket')
    def test_check_port_closed(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 111
        mock_socket_cls.return_value.__enter__.return_value = mock_socket

        result = NetworkToolbox.check_port("localhost", 8080)
        assert "is CLOSED" in result

    @patch('socket.gethostbyname')
    def test_dns_lookup_success(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "93.184.216.34"
        result = NetworkToolbox.dns_lookup("example.com")
        assert "DNS Lookup: example.com -> 93.184.216.34" in result

    @patch('socket.gethostbyname')
    def test_dns_lookup_failure(self, mock_gethostbyname):
        mock_gethostbyname.side_effect = Exception("Not found")
        result = NetworkToolbox.dns_lookup("nonexistent.domain")
        assert "Error resolving domain" in result

if __name__ == "__main__":
    pytest.main([__file__])
