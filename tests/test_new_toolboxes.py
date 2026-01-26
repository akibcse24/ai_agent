import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from crytonix.tools import NetworkToolbox, CryptoToolbox, ArchiveToolbox, HealthToolbox

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping(self, mock_run):
        mock_run.return_value.stdout = "Ping output"
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Ping output", result)

    @patch('socket.create_connection')
    def test_check_port_open(self, mock_socket):
        result = NetworkToolbox.check_port("google.com", 80)
        self.assertIn("is OPEN", result)

    @patch('socket.create_connection')
    def test_check_port_closed(self, mock_socket):
        mock_socket.side_effect = ConnectionRefusedError
        result = NetworkToolbox.check_port("localhost", 9999)
        self.assertIn("is CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "1.2.3.4"
        result = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("1.2.3.4", result)

class TestCryptoToolbox(unittest.TestCase):
    def test_generate_hash(self):
        result = CryptoToolbox.generate_hash("hello")
        self.assertIn("sha256", result)
        # sha256 of "hello" is 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        self.assertIn("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", result)

    def test_base64_encode_decode(self):
        encoded = CryptoToolbox.base64_encode("hello")
        self.assertIn("aGVsbG8=", encoded)
        decoded = CryptoToolbox.base64_decode("aGVsbG8=")
        self.assertIn("hello", decoded)

    def test_generate_uuid(self):
        uuid_str = CryptoToolbox.generate_uuid()
        self.assertEqual(len(uuid_str), 36)

class TestArchiveToolbox(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.test_dir, "file1.txt")
        with open(self.file1, "w") as f:
            f.write("content1")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_zip_unzip(self):
        zip_path = os.path.join(self.test_dir, "test.zip")
        # Test Zip
        result = ArchiveToolbox.zip_files(zip_path, [self.file1])
        self.assertIn("Successfully created", result)
        self.assertTrue(os.path.exists(zip_path))

        # Test Unzip
        extract_dir = os.path.join(self.test_dir, "extracted")
        result = ArchiveToolbox.unzip_file(zip_path, extract_dir)
        self.assertIn("Successfully extracted", result)
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "file1.txt")))

    def test_tar_untar(self):
        tar_path = os.path.join(self.test_dir, "test.tar.gz")
        # Test Tar
        result = ArchiveToolbox.create_tarball(tar_path, self.test_dir) # Tar the whole temp dir
        self.assertIn("Successfully created", result)
        self.assertTrue(os.path.exists(tar_path))

        # Test Untar
        extract_dir = os.path.join(self.test_dir, "extracted_tar")
        result = ArchiveToolbox.extract_tarball(tar_path, extract_dir)
        self.assertIn("Successfully extracted", result)
        # Check if files exist. Note: directory structure might be preserved
        self.assertTrue(os.path.exists(extract_dir))

class TestHealthToolbox(unittest.TestCase):
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Posture Check", result)

    def test_stretch_exercise(self):
        result = HealthToolbox.stretch_exercise()
        self.assertIn("Time to stretch", result)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Hydration Check", result)

    def test_take_break(self):
        result = HealthToolbox.take_break(10)
        self.assertIn("10 minutes", result)

if __name__ == '__main__':
    unittest.main()
