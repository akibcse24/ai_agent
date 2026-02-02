import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import zipfile
import subprocess

# Add parent directory to path to import crytonix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import (
    HealthToolbox, NetworkToolbox, ArchiveToolbox,
    CryptoToolbox, PDFToolbox, AudioToolbox
)

class TestHealthToolbox(unittest.TestCase):
    def test_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIn("Check your posture", result)

    def test_hydration_reminder(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIn("Time to hydrate", result)

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    def test_ping(self, mock_run):
        mock_run.return_value.stdout = "Reply from..."
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Ping successful", result)

        mock_run.side_effect = Exception("Ping error")
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Error pinging host", result)

    @patch('subprocess.run')
    def test_ping_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ping", timeout=10)
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Ping timed out", result)

    @patch('socket.socket')
    def test_check_port(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Open port
        mock_sock_instance.connect_ex.return_value = 0
        result = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("OPEN", result)

        # Closed port
        mock_sock_instance.connect_ex.return_value = 1
        result = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "1.2.3.4"
        result = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("1.2.3.4", result)

class TestArchiveToolbox(unittest.TestCase):
    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    def test_zip_files(self, mock_exists, mock_zipfile):
        mock_exists.return_value = True
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        result = ArchiveToolbox.zip_files("test.zip", ["file1.txt", "file2.txt"])
        self.assertIn("Successfully created test.zip", result)
        self.assertEqual(mock_zip_instance.write.call_count, 2)

    @patch('os.path.exists')
    def test_zip_files_missing(self, mock_exists):
        mock_exists.return_value = False
        result = ArchiveToolbox.zip_files("test.zip", ["missing.txt"])
        self.assertIn("Files not found", result)

    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_unzip_file(self, mock_makedirs, mock_exists, mock_zipfile):
        mock_exists.return_value = False
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # Mocking ZipInfo objects for Zip Slip check
        mock_member = MagicMock()
        mock_member.filename = "safe_file.txt"
        mock_zip_instance.infolist.return_value = [mock_member]

        result = ArchiveToolbox.unzip_file("test.zip", "output_dir")
        self.assertIn("Successfully extracted", result)
        mock_zip_instance.extractall.assert_called_with("output_dir")

class TestCryptoToolbox(unittest.TestCase):
    def test_generate_hash(self):
        result = CryptoToolbox.generate_hash("hello", "md5")
        # md5("hello") = 5d41402abc4b2a76b9719d911017c592
        self.assertEqual(result, "5d41402abc4b2a76b9719d911017c592")

        result = CryptoToolbox.generate_hash("hello", "sha256")
        self.assertEqual(len(result), 64)

    def test_base64(self):
        text = "Hello World"
        encoded = CryptoToolbox.base64_encode(text)
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual(decoded, text)

    def test_generate_uuid(self):
        uuid_val = CryptoToolbox.generate_uuid()
        self.assertEqual(len(uuid_val.split('-')), 5)

class TestPDFToolbox(unittest.TestCase):
    def test_extract_text_missing_dep(self):
        with patch.dict(sys.modules, {'pypdf': None}):
            result = PDFToolbox.extract_text("test.pdf")
            self.assertIn("pypdf not installed", result)

    def test_extract_text_success(self):
        # Mock pypdf.PdfReader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted Page Text"
        mock_reader.pages = [mock_page]

        with patch.dict(sys.modules, {'pypdf': MagicMock()}):
            with patch('pypdf.PdfReader', return_value=mock_reader):
                # We need to ensure that the import inside the function sees our mock
                # Since imports are cached, patch.dict might not work if already imported?
                # Actually, local imports inside functions are re-executed if not in sys.modules,
                # but if we patch sys.modules, it should work.

                # However, since we might have imported pypdf elsewhere or not, let's just patch the class where it's used.
                # But it's imported INSIDE the method.

                # To test local import mocking effectively:
                with patch.dict(sys.modules, {'pypdf': MagicMock(PdfReader=MagicMock(return_value=mock_reader))}):
                    result = PDFToolbox.extract_text("test.pdf")
                    # If pypdf is installed in env, the local import might pick it up unless we mock it well.
                    # Since we are running in an env where pypdf IS NOT installed, patching sys.modules should provide the mock.
                    pass

        # A more robust way to test success when pypdf is NOT installed is:
        mock_module = MagicMock()
        mock_module.PdfReader.return_value.pages = [MagicMock(extract_text=lambda: "Page 1")]

        with patch.dict(sys.modules, {'pypdf': mock_module}):
             result = PDFToolbox.extract_text("test.pdf")
             self.assertIn("Page 1", result)

    def test_merge_pdfs_missing_dep(self):
        with patch.dict(sys.modules, {'pypdf': None}):
            result = PDFToolbox.merge_pdfs("out.pdf", ["in.pdf"])
            self.assertIn("pypdf not installed", result)

class TestAudioToolbox(unittest.TestCase):
    def test_tts_missing_dep(self):
        with patch.dict(sys.modules, {'pyttsx3': None}):
            result = AudioToolbox.text_to_speech("hello")
            self.assertIn("pyttsx3 not installed", result)

    def test_metadata_missing_dep(self):
        with patch.dict(sys.modules, {'mutagen': None}):
            result = AudioToolbox.get_metadata("song.mp3")
            self.assertIn("mutagen not installed", result)

if __name__ == '__main__':
    unittest.main()
