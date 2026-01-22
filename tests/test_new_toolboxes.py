import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure crytonix is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import HealthToolbox, NetworkToolbox

class TestHealthToolbox(unittest.TestCase):
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Sit up straight", result)

    def test_stretch_exercise(self):
        result = HealthToolbox.stretch_exercise()
        self.assertIn("stretch_exercise", result)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Time to hydrate", result)

    def test_take_break(self):
        result = HealthToolbox.take_break(10)
        self.assertIn("10-minute break", result)

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping(self, mock_subprocess_run):
        mock_subprocess_run.return_value.stdout = "PING google.com (142.250.190.46) 56(84) bytes of data."
        result = NetworkToolbox.ping("google.com")
        self.assertIn("PING google.com", result)
        mock_subprocess_run.assert_called_once()

    @patch('socket.socket')
    def test_check_port_open(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket
        mock_socket.connect_ex.return_value = 0 # Success

        result = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("OPEN", result)

    @patch('socket.socket')
    def test_check_port_closed(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket
        mock_socket.connect_ex.return_value = 111 # Connection refused

        result = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "1.2.3.4"
        result = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("1.2.3.4", result)

if __name__ == '__main__':
    unittest.main()
