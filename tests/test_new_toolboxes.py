import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from crytonix.tools import (NetworkToolbox, ArchiveToolbox, CryptoToolbox,
                           HealthToolbox, PDFToolbox, AudioToolbox)

class TestNewToolboxes(unittest.TestCase):

    # --- NetworkToolbox Tests ---
    @patch('subprocess.run')
    @patch('platform.system')
    def test_network_ping(self, mock_platform, mock_run):
        mock_platform.return_value = 'Linux'
        mock_run.return_value = MagicMock(returncode=0, stdout="Ping success")

        result = NetworkToolbox.ping("google.com")
        self.assertIn("Ping successful", result)
        mock_run.assert_called()

    @patch('socket.socket')
    def test_network_check_port(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 0 # Open

        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("is OPEN", result)

        mock_sock_instance.connect_ex.return_value = 1 # Closed
        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("is CLOSED", result)

    @patch('socket.gethostbyname')
    def test_network_dns_lookup(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "127.0.0.1"
        result = NetworkToolbox.dns_lookup("localhost")
        self.assertIn("127.0.0.1", result)

    # --- ArchiveToolbox Tests ---
    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    def test_archive_zip_files(self, mock_exists, mock_zipfile):
        mock_exists.return_value = True
        result = ArchiveToolbox.zip_files(["test.txt"], "out.zip")
        self.assertIn("Successfully created out.zip", result)

    @patch('zipfile.ZipFile')
    def test_archive_unzip_file(self, mock_zipfile):
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        # Test valid unzip
        mock_zip.namelist.return_value = ["file.txt"]
        result = ArchiveToolbox.unzip_file("test.zip", "extract_dir")
        self.assertIn("Successfully extracted", result)

        # Test Zip Slip
        mock_zip.namelist.return_value = ["../evil.txt"]
        result = ArchiveToolbox.unzip_file("test.zip", "extract_dir")
        self.assertIn("Attempted Zip Slip", result)

    # --- CryptoToolbox Tests ---
    def test_crypto_hash(self):
        result = CryptoToolbox.generate_hash("hello", "md5")
        self.assertEqual(len(result), 32) # MD5 is 32 chars hex

        result = CryptoToolbox.generate_hash("hello", "sha256")
        self.assertEqual(len(result), 64) # SHA256 is 64 chars hex

    def test_crypto_base64(self):
        encoded = CryptoToolbox.base64_encode("hello")
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual(decoded, "hello")

    def test_crypto_uuid(self):
        uuid = CryptoToolbox.generate_uuid()
        self.assertEqual(len(uuid.split("-")), 5)

    # --- HealthToolbox Tests ---
    def test_health_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Posture Check", result)

    def test_health_hydration(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Hydration Check", result)

    # --- PDFToolbox Tests ---
    def test_pdf_missing_deps(self):
        # Mock sys.modules to simulate missing dependencies
        with patch.dict(sys.modules, {'pypdf': None}):
            result = PDFToolbox.extract_text("test.pdf")
            self.assertIn("not installed", result)

    @patch('pypdf.PdfReader')
    def test_pdf_extract_text(self, mock_reader):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page content"
        mock_reader.return_value.pages = [mock_page]

        result = PDFToolbox.extract_text("test.pdf")
        self.assertIn("Page content", result)

    # --- AudioToolbox Tests ---
    def test_audio_missing_deps(self):
        with patch.dict(sys.modules, {'pyttsx3': None}):
            result = AudioToolbox.text_to_speech("hello")
            self.assertIn("not installed", result)

    @patch('pyttsx3.init')
    def test_audio_tts(self, mock_init):
        mock_engine = MagicMock()
        mock_init.return_value = mock_engine

        result = AudioToolbox.text_to_speech("hello")
        self.assertIn("Saved audio", result)
        mock_engine.save_to_file.assert_called()

if __name__ == '__main__':
    unittest.main()
