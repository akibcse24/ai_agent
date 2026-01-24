import pytest
from unittest.mock import patch, MagicMock
from crytonix.tools import HealthToolbox, NetworkToolbox

class TestHealthToolbox:
    @patch('crytonix.tools.random.choice')
    def test_check_posture(self, mock_choice):
        mock_choice.return_value = "Straighten your back!"
        result = HealthToolbox.check_posture()
        assert "Straighten your back!" in result
        assert "🧘 Posture Check:" in result

    @patch('crytonix.tools.random.choice')
    def test_stretch_exercise(self, mock_choice):
        mock_choice.return_value = "Neck Roll: Gently roll your head in a circle."
        result = HealthToolbox.stretch_exercise()
        assert "Neck Roll" in result
        assert "🤸 Stretch Time:" in result

    @patch('crytonix.tools.random.choice')
    def test_hydration_reminder(self, mock_choice):
        mock_choice.return_value = "Water break! 🚰"
        result = HealthToolbox.hydration_reminder()
        assert result == "Water break! 🚰"

    @patch('crytonix.tools.random.choice')
    def test_take_break(self, mock_choice):
        mock_choice.return_value = "Walk around the room."
        result = HealthToolbox.take_break("10 minutes")
        assert "Take a 10 minutes break" in result
        assert "Walk around the room." in result

class TestNetworkToolbox:
    @patch('crytonix.tools.subprocess.run')
    def test_ping_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Reply from 127.0.0.1: bytes=32 time<1ms TTL=128"
        mock_run.return_value = mock_result

        result = NetworkToolbox.ping("localhost")
        assert "✅ Ping localhost successful" in result
        assert "Reply from" in result

    @patch('crytonix.tools.subprocess.run')
    def test_ping_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Request timed out."
        mock_run.return_value = mock_result

        result = NetworkToolbox.ping("invalid.host")
        assert "❌ Ping invalid.host failed" in result

    @patch('crytonix.tools.socket.socket')
    def test_check_port_open(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_cls.return_value = mock_sock

        result = NetworkToolbox.check_port("localhost", 80)
        assert "✅ Port 80 on localhost is OPEN" in result
        mock_sock.close.assert_called_once()

    @patch('crytonix.tools.socket.socket')
    def test_check_port_closed(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111
        mock_socket_cls.return_value = mock_sock

        result = NetworkToolbox.check_port("localhost", 9999)
        assert "❌ Port 9999 on localhost is CLOSED" in result
        mock_sock.close.assert_called_once()

    @patch('crytonix.tools.socket.gethostbyname')
    def test_dns_lookup_success(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "93.184.216.34"
        result = NetworkToolbox.dns_lookup("example.com")
        assert "🌐 DNS Lookup: example.com -> 93.184.216.34" in result

    @patch('crytonix.tools.socket.gethostbyname')
    def test_dns_lookup_failure(self, mock_gethostbyname):
        mock_gethostbyname.side_effect = Exception("gaierror")
        result = NetworkToolbox.dns_lookup("invalid-domain.com")
        assert "Error resolving invalid-domain.com" in result
