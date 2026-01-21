import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crytonix.tools import HealthToolbox, NetworkToolbox

class TestHealthToolbox(unittest.TestCase):
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Posture Check", result)

    def test_stretch_exercise(self):
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "Mock Stretch"
            result = HealthToolbox.stretch_exercise()
            self.assertIn("Stretch Break: Mock Stretch", result)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Hydration Check", result)

    def test_take_break(self):
        result = HealthToolbox.take_break(10)
        self.assertIn("10 minutes", result)

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping_success(self, mock_run):
        mock_run.return_value.stdout = "Reply from 127.0.0.1"
        result = NetworkToolbox.ping("127.0.0.1")
        self.assertIn("Ping results for 127.0.0.1", result)
        self.assertIn("Reply from 127.0.0.1", result)

    @patch('socket.socket')
    def test_check_port_open(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 0

        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("OPEN", result)

    @patch('socket.socket')
    def test_check_port_closed(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 111

        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "1.2.3.4"
        result = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("DNS Lookup: example.com -> 1.2.3.4", result)
