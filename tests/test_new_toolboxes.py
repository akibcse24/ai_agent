import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import crytonix if running as script,
# but pytest usually handles this.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import HealthToolbox, NetworkToolbox, ArchiveToolbox, CryptoToolbox

class TestHealthToolbox(unittest.TestCase):
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Posture Check", result)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Hydration Check", result)

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping(self, mock_run):
        mock_run.return_value.stdout = "Ping output"
        result = NetworkToolbox.ping("google.com")
        self.assertEqual(result, "Ping output")
        mock_run.assert_called_once()

    @patch('socket.create_connection')
    def test_check_port_open(self, mock_connect):
        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("OPEN", result)

    @patch('socket.create_connection')
    def test_check_port_closed(self, mock_connect):
        import socket
        mock_connect.side_effect = socket.timeout
        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethost):
        mock_gethost.return_value = "127.0.0.1"
        result = NetworkToolbox.dns_lookup("localhost")
        self.assertIn("127.0.0.1", result)

class TestArchiveToolbox(unittest.TestCase):
    def setUp(self):
        # Create dummy files
        with open("test1.txt", "w") as f: f.write("content1")
        with open("test2.txt", "w") as f: f.write("content2")

    def tearDown(self):
        for f in ["test1.txt", "test2.txt", "test.zip", "test.tar.gz"]:
            if os.path.exists(f): os.remove(f)
        import shutil
        if os.path.exists("extracted"): shutil.rmtree("extracted")

    def test_zip_unzip(self):
        # Zip
        res = ArchiveToolbox.zip_files(["test1.txt", "test2.txt"], "test.zip")
        self.assertIn("Created zip", res)
        self.assertTrue(os.path.exists("test.zip"))

        # Unzip
        res = ArchiveToolbox.unzip_file("test.zip", "extracted")
        self.assertIn("Extracted", res)
        self.assertTrue(os.path.exists("extracted/test1.txt"))
        self.assertTrue(os.path.exists("extracted/test2.txt"))

    def test_tar_untar(self):
        # Tar
        res = ArchiveToolbox.create_tarball(["test1.txt", "test2.txt"], "test.tar.gz")
        self.assertIn("Created tarball", res)
        self.assertTrue(os.path.exists("test.tar.gz"))

        # Untar
        res = ArchiveToolbox.extract_tarball("test.tar.gz", "extracted")
        self.assertIn("Extracted", res)
        self.assertTrue(os.path.exists("extracted/test1.txt"))

class TestCryptoToolbox(unittest.TestCase):
    def test_generate_hash(self):
        res = CryptoToolbox.generate_hash("hello", "md5")
        # md5 of hello is 5d41402abc4b2a76b9719d911017c592
        self.assertIn("5d41402abc4b2a76b9719d911017c592", res)

    def test_base64(self):
        text = "Hello World"
        encoded = CryptoToolbox.base64_encode(text)
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual(text, decoded)

    def test_uuid(self):
        u = CryptoToolbox.generate_uuid()
        self.assertEqual(len(u.split('-')), 5)

if __name__ == '__main__':
    unittest.main()
