import os
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import crytonix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import NetworkToolbox, CryptoToolbox, ArchiveToolbox, HealthToolbox

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Reply from 127.0.0.1")
        result = NetworkToolbox.ping("127.0.0.1")
        self.assertIn("successful", result)
        self.assertIn("Reply from", result)

    @patch('socket.socket')
    def test_check_port_open(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance

        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("OPEN", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "1.2.3.4"
        result = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("1.2.3.4", result)

class TestCryptoToolbox(unittest.TestCase):
    def test_generate_hash(self):
        text = "hello"
        result = CryptoToolbox.generate_hash(text, "md5")
        # md5 of "hello" is 5d41402abc4b2a76b9719d911017c592
        self.assertIn("5d41402abc4b2a76b9719d911017c592", result)

    def test_base64(self):
        text = "hello world"
        encoded = CryptoToolbox.base64_encode(text)
        self.assertIn("aGVsbG8gd29ybGQ=", encoded)

        decoded = CryptoToolbox.base64_decode("aGVsbG8gd29ybGQ=")
        self.assertIn("hello world", decoded)

    def test_uuid(self):
        result = CryptoToolbox.generate_uuid()
        self.assertIn("UUID:", result)
        self.assertEqual(len(result.split(": ")[1]), 36)

class TestArchiveToolbox(unittest.TestCase):
    def setUp(self):
        self.test_files = ["test1.txt", "test2.txt"]
        for f in self.test_files:
            with open(f, "w") as file:
                file.write("content")

    def tearDown(self):
        for f in self.test_files:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists("test_archive.zip"):
            os.remove("test_archive.zip")
        if os.path.exists("test_archive.tar.gz"):
            os.remove("test_archive.tar.gz")

    def test_zip_files(self):
        result = ArchiveToolbox.zip_files(self.test_files, "test_archive")
        self.assertIn("Created zip archive", result)
        self.assertTrue(os.path.exists("test_archive.zip"))

    def test_tar_files(self):
        result = ArchiveToolbox.create_tarball(self.test_files, "test_archive")
        self.assertIn("Created tarball", result)
        self.assertTrue(os.path.exists("test_archive.tar.gz"))

class TestHealthToolbox(unittest.TestCase):
    def test_methods_return_string(self):
        self.assertIsInstance(HealthToolbox.check_posture(), str)
        self.assertIsInstance(HealthToolbox.hydration_reminder(), str)
        self.assertIsInstance(HealthToolbox.take_break(), str)

if __name__ == '__main__':
    unittest.main()
