import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Ensure crytonix is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crytonix.tools import NetworkToolbox, ArchiveToolbox, CryptoToolbox, HealthToolbox

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Pong", returncode=0)
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Pong", result)

    @patch('subprocess.run')
    def test_ping_failure(self, mock_run):
        mock_run.side_effect = Exception("Ping error")
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Error pinging host", result)

    @patch('socket.socket')
    def test_check_port_open(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("OPEN", result)

    @patch('socket.socket')
    def test_check_port_closed(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 1
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup_success(self, mock_gethost):
        mock_gethost.return_value = "127.0.0.1"
        result = NetworkToolbox.dns_lookup("localhost")
        self.assertIn("127.0.0.1", result)

class TestArchiveToolbox(unittest.TestCase):
    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    def test_zip_files(self, mock_exists, mock_zip):
        mock_exists.return_value = True
        result = ArchiveToolbox.zip_files("test.zip", ["file1.txt"])
        self.assertIn("Successfully created", result)
        mock_zip.assert_called()

    @patch('zipfile.ZipFile')
    def test_unzip_file(self, mock_zip):
        # Setup mock to return a safe file in namelist
        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = ["safe.txt"]
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        result = ArchiveToolbox.unzip_file("test.zip")
        self.assertIn("Successfully extracted", result)
        mock_zip.assert_called()

    @patch('zipfile.ZipFile')
    def test_unzip_file_zip_slip(self, mock_zip):
        # Setup mock to return a malicious file in namelist
        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = ["../../evil.sh"]
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        result = ArchiveToolbox.unzip_file("test.zip")
        self.assertIn("Zip Slip attack", result)

class TestCryptoToolbox(unittest.TestCase):
    def test_generate_hash(self):
        result = CryptoToolbox.generate_hash("hello", "sha256")
        # SHA256 of "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(result, expected)

    def test_base64_encode(self):
        result = CryptoToolbox.base64_encode("hello")
        self.assertEqual(result, "aGVsbG8=")

    def test_base64_decode(self):
        result = CryptoToolbox.base64_decode("aGVsbG8=")
        self.assertEqual(result, "hello")

    def test_generate_uuid(self):
        result = CryptoToolbox.generate_uuid()
        self.assertEqual(len(result), 36)

class TestHealthToolbox(unittest.TestCase):
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Posture Check", result)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Time to hydrate", result)

if __name__ == '__main__':
    unittest.main()
