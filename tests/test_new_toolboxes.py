import unittest
import sys
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

# Ensure the package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crytonix.tools import (
    HealthToolbox, NetworkToolbox, ArchiveToolbox, CryptoToolbox,
    PDFToolbox, AudioToolbox
)

class TestNewToolboxes(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # --- HealthToolbox Tests ---
    def test_health_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIsInstance(result, str)
        self.assertIn("Posture Check", result)

    def test_health_hydration(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIsInstance(result, str)
        self.assertIn("Hydration Check", result)

    # --- NetworkToolbox Tests ---
    @patch("subprocess.run")
    def test_network_ping(self, mock_run):
        mock_run.return_value.stdout = "Ping statistics"
        mock_run.return_value.returncode = 0

        result = NetworkToolbox.ping("127.0.0.1", count=1)

        self.assertIn("Ping statistics", result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], 'ping')
        self.assertEqual(args[3], '127.0.0.1')

    @patch("socket.create_connection")
    def test_network_check_port_open(self, mock_socket):
        # Connection succeeds (context manager doesn't raise)
        mock_socket.return_value.__enter__.return_value = None

        result = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("OPEN", result)

    @patch("socket.create_connection", side_effect=ConnectionRefusedError)
    def test_network_check_port_closed(self, mock_socket):
        result = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("CLOSED", result)

    @patch("socket.gethostbyname")
    def test_network_dns_lookup(self, mock_dns):
        mock_dns.return_value = "192.168.1.1"
        result = NetworkToolbox.dns_lookup("test.local")
        self.assertIn("192.168.1.1", result)

    # --- ArchiveToolbox Tests ---
    def test_archive_zip_unzip(self):
        # Create a dummy file structure
        src_dir = os.path.join(self.test_dir, "source")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "file1.txt"), "w") as f:
            f.write("content 1")
        with open(os.path.join(src_dir, "file2.txt"), "w") as f:
            f.write("content 2")

        zip_path = os.path.join(self.test_dir, "archive.zip")

        # Test Zip
        result_zip = ArchiveToolbox.zip_files(src_dir, zip_path)
        self.assertIn("Successfully created", result_zip)
        self.assertTrue(os.path.exists(zip_path))

        # Test Unzip
        extract_dir = os.path.join(self.test_dir, "extracted")
        result_unzip = ArchiveToolbox.unzip_file(zip_path, extract_dir)
        self.assertIn("Successfully extracted", result_unzip)

        # Because we zipped a folder, the zip contains the folder name structure
        extracted_source = os.path.join(extract_dir, "source")
        self.assertTrue(os.path.exists(os.path.join(extracted_source, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(extracted_source, "file2.txt")))
        with open(os.path.join(extracted_source, "file1.txt"), "r") as f:
            self.assertEqual(f.read(), "content 1")

    # --- CryptoToolbox Tests ---
    def test_crypto_hash(self):
        text = "hello"
        # sha256 of "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        result = CryptoToolbox.generate_hash(text)
        self.assertEqual(result, expected)

    def test_crypto_file_hash(self):
        filepath = os.path.join(self.test_dir, "hash_me.txt")
        with open(filepath, "w") as f:
            f.write("hello")

        # Write binary to be sure
        with open(filepath, "wb") as f:
            f.write(b"hello")

        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        result = CryptoToolbox.generate_file_hash(filepath)
        self.assertEqual(result, expected)

    def test_crypto_base64(self):
        text = "hello world"
        encoded = CryptoToolbox.base64_encode(text)
        self.assertEqual(encoded, "aGVsbG8gd29ybGQ=")
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual(text, decoded)

    def test_crypto_uuid(self):
        uuid1 = CryptoToolbox.generate_uuid()
        uuid2 = CryptoToolbox.generate_uuid()
        self.assertNotEqual(uuid1, uuid2)
        # Simple UUID format check
        self.assertEqual(len(uuid1), 36)
        self.assertIn("-", uuid1)

    # --- Multimedia Tests (Graceful Degradation or Mock) ---

    def test_pdf_dependencies_missing(self):
        """Test that it reports error when pypdf is missing."""
        # Use patch to ensure import fails by assigning None to the module
        with patch.dict(sys.modules, {'pypdf': None}):
            result = PDFToolbox.extract_text("dummy.pdf")
            self.assertIn("Error: pypdf not installed", result)

    def test_audio_dependencies_missing(self):
        """Test that it reports error when pyttsx3 is missing."""
        with patch.dict(sys.modules, {'pyttsx3': None}):
            result = AudioToolbox.text_to_speech("Test")
            self.assertIn("Error: pyttsx3 not installed", result)

if __name__ == '__main__':
    unittest.main()
